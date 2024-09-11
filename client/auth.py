from http.client import HTTPException

from hubspot import HubSpot
from hubspot.auth import oauth
from hubspot.crm.owners import PublicOwner

from client.config import HUBSPOT_CLIENT_SECRET, HUBSPOT_REDIRECT_URL, HUBSPOT_CLIENT_ID, OAUTH_DATA_TOKEN_TYPE_OAUTH


def handle_get_request_for_hubspot_oauth_redirect(code: str, state: Optional[str]) -> str:
    print(f"HUBSPOT OAUTH REDIRECT EVENT: {code}")

    authorization_code = code
    client_secret = HUBSPOT_CLIENT_SECRET
    # TODO(p2, devx): We should move this into app.HubspotClient once our deployments are more consolidated.
    api_client = HubSpot()
    try:
        tokens = api_client.auth.oauth.tokens_api.create(
            grant_type="authorization_code",
            redirect_uri=HUBSPOT_REDIRECT_URL,
            client_id=HUBSPOT_CLIENT_ID,
            client_secret=client_secret,
            # This is a one-time authorization code to get access and refresh tokens - so don't screw up.
            code=authorization_code,
        )
    except oauth.ApiException as e:
        raise HTTPException(
            500, f"Exception when fetching access token from HubSpot: {e}"
        )
    api_client.access_token = tokens.access_token

    # We rather have multiple OauthData entries for the same refresh_token then trying to have a normalized structure.
    oauth_data_id = OauthData.insert(
        token_type=OAUTH_DATA_TOKEN_TYPE_OAUTH,
    ).execute()
    OauthData.update_safely(
        oauth_data_id=oauth_data_id,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )

    # == SECOND, we check all their accounts to see if they are part of any organization already
    # List[PublicOwner]
    owners_response = api_client.crm.owners.get_all()
    accounts = account.Account.get_or_onboard_for_hubspot(
        owners_response=owners_response
    )
    assert len(accounts) > 0

    accounts_with_no_org_id = []
    unique_org_ids = set()
    for acc in accounts:
        if acc.organization_id is None:
            accounts_with_no_org_id.append(acc)
        else:
            unique_org_ids.add(acc.organization_id)
    print(
        f"Success fetching Hubspot owners data, total count {len(accounts)} "
        f"from which accounts with no orgs {len(accounts_with_no_org_id)}"
    )

    if len(unique_org_ids) == 0:
        print("Org onboard: None of the Hubspot accounts have a organization")
    elif len(unique_org_ids) == 1:
        print(
            f"Org onboard: Found one organization among Hubspot accounts: {unique_org_ids}"
        )
    else:
        print(
            f"WARNING: Potential trouble linking HubSpot organization when accounts have multiple orgs {unique_org_ids}"
        )

    # == THIRD, we check through HubId if an organization already exists (as an idempotency_key).
    # AccessTokenInfoResponse
    org_metadata = api_client.auth.oauth.access_tokens_api.get(api_client.access_token)
    print(f"org_metadata={org_metadata}")
    external_org_id = org_metadata.hub_id
    external_org_admin_email = org_metadata.user
    external_org_name = org_metadata.hub_domain
    existing_pipeline = Pipeline.get_or_none_for_external_org_id(
        external_org_id, DESTINATION_HUBSPOT_ID
    )

    # == FOURTH, we check for the admin account if that has an organization or not
    # NOTE: admin_account_id can be None
    admin_account_id = _parse_account_id_from_state_param(state)
    if admin_account_id is None:
        print(
            f"Trying to get admin account for hubspot oauth linker {external_org_admin_email}"
        )
        admin_account = account.Account.get_by_email_or_none(external_org_admin_email)
        if bool(admin_account):
            admin_account_id = admin_account.id
    else:
        admin_account = account.Account.get_by_id(admin_account_id)

    # == AFTER all the prep work looking for idempotency_id we decide if create a new org or reuse an existing one
    if bool(admin_account) and bool(admin_account.organization_id):
        print(
            f"Org Decision: will be using organization of admin account {admin_account}"
        )
        org = admin_account.organization
    elif bool(existing_pipeline):
        print(
            f"Org Decision: will be using organization of the existing pipeline {existing_pipeline}"
        )
        org = existing_pipeline.organization
    else:
        print("Org Decision: creating a new org")
        org = Organization.get_or_create_for_account_id(
            admin_account_id, name=external_org_name
        )
    print(f"CHOSEN ORGANIZATION: {org}")

    # Update pipeline
    pipeline = Pipeline.get_or_create_for(
        external_org_id, org.id, DESTINATION_HUBSPOT_ID
    )
    # Here we deliberately allow to override the refresh_token, as we might need to re-auth time-to-time.
    if pipeline.oauth_data_id != oauth_data_id:
        od1 = OauthData.get_by_id(pipeline.oauth_data_id)
        od2 = OauthData.get_by_id(oauth_data_id)
        if od1.refresh_token != od2.refresh_token:
            print(
                f"WARNING: different refresh token given through oauth than in use for pipeline {pipeline.id}"
                f", check new oauth_data_id={oauth_data_id} and old {pipeline.oauth_data_id}"
            )
    pipeline.oauth_data_id = oauth_data_id
    print(f"setting pipeline.oauth_data_id to {oauth_data_id}")

    if pipeline.external_org_id is None:
        pipeline.external_org_id = org_metadata.hub_id
        print(f"setting pipeline.external_org_id to {pipeline.external_org_id}")
    pipeline.save()

    # Update org
    if org.name is None:
        print(f"setting org.name to {external_org_name}")
        org.name = external_org_name
    org.save()

    # Update account
    # TODO(P2, devx): Feels like Account<->Organization should have a link object to - with metadata.
    #   Or it something feels off of having both Organization and Pipeline.
    for acc in accounts:
        if acc.organization_id is None:
            acc.organization_id = org.id
        elif acc.organization_id != org.id:
            print(f"WARNING: account part of another organization {acc}")
        if acc.organization_role is None:  # to not over-write an "owner"
            acc.organization_role = (
                ORGANIZATION_ROLE_OWNER
                if acc.id == admin_account_id
                else ORGANIZATION_ROLE_CONTRIBUTOR
            )
        acc.save()

    return f"https://app.dumpsheet.com?hubspot_status=success&account_id={admin_account_id}"

def get_or_onboard_for_hubspot(
    owners_response: Optional[List[PublicOwner]],
) -> List["Account"]:
    if owners_response is None or not isinstance(owners_response, list):
        print(
            f"WARNING: Unexpected owners_response {type(owners_response)}: {owners_response}"
        )
        return []

    print(f"Gonna onboard *up to* {len(owners_response)} Hubspot accounts")
    accounts = []
    for owner in owners_response:
        if not isinstance(owner, PublicOwner):
            print(f"WARNING: Unexpected owner structure {type(owner)}: {owner}")
            continue

        # Since the no-login onboarding is already quite complex, we will just do the simple thing here.
        full_name = f"{owner.first_name} {owner.last_name}"
        acc = Account.get_or_onboard_for_email(
            email=owner.email,
            full_name=full_name,
            utm_source="hubspot_app",
        )
        if acc.organization_user_id is None:
            # TODO(P2, devx): For this, it makes more sense to have acc <-> pipeline.
            acc.organization_user_id = owner.id  # not user_id, we allow overwrites
            acc.save()
        accounts.append(acc)
        print(
            f"Hubspot owner creation success - yielded account {acc} for email {owner.email}"
        )

    return accounts