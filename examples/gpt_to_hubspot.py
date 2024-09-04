# To get an idea, this is something https://hints.so/ and similar sites do.

import time
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Dict, List, Optional

from hubspot.crm.properties import ModelProperty

from app.form_library import get_form
from app.hubspot_client import HubspotClient
from app.hubspot_models import (
    ALLOWED_FIELDS,
    AssociationType,
    FieldDefinition,
    FieldNames,
    HubspotObject,
    ObjectType,
)
from common.config import POSTGRES_LOGIN_URL_FROM_ENV
from common.form import FormData, FormDefinition, FormName
from gpt_form_filler.openai_client import OpenAiClient

from common.gpt_client import open_ai_client_with_db_cache
from database.account import Account
from supawee.client import connect_to_postgres
from database.constants import DESTINATION_HUBSPOT_ID, OAUTH_DATA_TOKEN_TYPE_OAUTH
from database.email_log import EmailLog
from database.models import BaseDataEntry, BaseOrganization
from database.oauth_data import OauthData
from database.organization import Organization
from database.pipeline import Pipeline


# Feels like "app.result"
KEY_HUBSPOT_CONTACT = "hubspot_contact"
KEY_HUBSPOT_CALL = "hubspot_call"
KEY_HUBSPOT_TASK = "hubspot_task"


def _count_set_fields(form_data: FormData) -> int:
    return sum(1 for value in form_data.to_dict() if value is not None)


# TODO(P1, devx): REFACTOR: We should wrap this into a HubspotObject for extra validation,
#  * essentially take that code from extract_form_data and put it there.
def _maybe_add_hubspot_owner_id(form_data: FormData, hubspot_owner_id):
    if bool(form_data) and bool(hubspot_owner_id):
        int_hubspot_owner_id = None
        try:
            int_hubspot_owner_id = int(hubspot_owner_id)
            form_data.set_field_value(
                FieldNames.HUBSPOT_OWNER_ID.value, int_hubspot_owner_id
            )
        except Exception as ex:
            print(
                f"WARNING: Cannot set hubspot_owner_id {int_hubspot_owner_id} cause {ex}"
            )
            pass


# TODO: hubspot_owner_id might need to be int
def extract_and_sync_contact_with_follow_up(
    client: HubspotClient,
    gpt_client: OpenAiClient,
    db_task: Task,
    text: str,
    hub_id: Optional[str] = None,
    hubspot_owner_id: Optional[int] = None,
    local_hack=False,
) -> HubspotDataEntry:
    # When too little text, then don't even try.
    if len(str(text)) < 50:
        print(f"WARNING: transcript too short to infer data: {text}")
        return HubspotDataEntry(
            transcript=text,
            state="short",
        )

    # CONTACT CREATION
    contact_form = get_form(FormName.HUBSPOT_CONTACT)
    # TODO(P1, gpt-form-filler migration): We lost task_id=db_task.id which was nice for tracking
    contact_form_data, contact_err = gpt_client.fill_in_form(form=contact_form, text=text)
    _maybe_add_hubspot_owner_id(contact_form_data, hubspot_owner_id)
    db_task.add_generated_output(KEY_HUBSPOT_CONTACT, contact_form_data)

    # When it would yield too little information, rather skip and make them re-enter.
    if _count_set_fields(contact_form_data) <= 1:
        print(
            f"fWARNING: incomplete data entry as too little fields filled for {contact_form_data} from text: {text}"
        )
        return HubspotDataEntry(
            transcript=text,
            state="incomplete",
        )

    # TODO(P1, ux): Figure out if you can create contacts without a communication channel
    if local_hack:
        # Just mock new contact for every run
        if bool(contact_form_data):
            contact_form_data.set_field_value(
                FieldNames.EMAIL.value, f"example{int(time.time())}@gmail.com"
            )
            contact_form_data.set_field_value(
                FieldNames.PHONE.value, f"+1650210{int(time.time()) % 10000}"
            )

    contact_response = client.crm_contact_create(contact_form_data.to_dict())
    db_task.add_sync_response(
        KEY_HUBSPOT_CONTACT,
        contact_response.status,
        contact_response.get_task_response(),
    )
    contact_id = contact_response.hs_object_id

    # CALL CREATION
    call_form = get_form(FormName.HUBSPOT_MEETING)
    # use_current_time so hs_timestamp gets filled
    # TODO(P2, gpt-form-filler migration): We lost task_id=db_task.id which was nice for tracking
    call_form_data, call_err = gpt_client.fill_in_form(form=call_form, text=text, use_current_time=True)
    _maybe_add_hubspot_owner_id(call_form_data, hubspot_owner_id)
    db_task.add_generated_output(KEY_HUBSPOT_CALL, call_form_data)

    call_response = client.crm_call_create(call_form_data.to_dict())
    db_task.add_sync_response(
        KEY_HUBSPOT_CALL, call_response.status, call_response.get_task_response()
    )
    call_id = call_response.hs_object_id

    # TASK CREATION
    # TODO(P1, ux): Sometimes, there might be no task.
    hs_task_form = get_form(FormName.HUBSPOT_TASK)
    # use_current_time so hs_timestamp gets filled
    # TODO(P2, gpt-form-filler migration): We lost task_id=db_task.id which was nice for tracking
    hs_task_data, hs_task_err = gpt_client.fill_in_form(form=hs_task_form, text=text, use_current_time=True)
    _maybe_add_hubspot_owner_id(hs_task_data, hubspot_owner_id)
    db_task.add_generated_output(KEY_HUBSPOT_TASK, hs_task_data)

    hs_task_response = client.crm_task_create(hs_task_data.to_dict())
    db_task.add_sync_response(
        KEY_HUBSPOT_TASK, hs_task_response.status, hs_task_response.get_task_response()
    )
    hs_task_id = hs_task_response.hs_object_id

    # ASSOCIATION CREATION
    contact_to_call_result = None
    if bool(contact_id) and bool(call_id):
        contact_to_call_result = client.crm_association_create(
            "contact", contact_id, "call", call_id, AssociationType.CONTACT_TO_CALL
        )
    contact_to_task_result = None
    if bool(contact_id) and bool(hs_task_id):
        contact_to_task_result = client.crm_association_create(
            "contact", contact_id, "task", hs_task_id, AssociationType.CONTACT_TO_TASK
        )

    if (
        contact_response.is_success()
        and call_response.is_success()
        and hs_task_response.is_success()
    ):
        state = "success"
    else:
        if contact_form_data is None or call_form_data is None or hs_task_data is None:
            state = "error_gpt"
        elif contact_response.status == HTTPStatus.CONFLICT:
            state = "warning_already_created"
        else:
            state = "error_hubspot_sync"

    db_task.finish()

    # There are a few columns sets for the same object_type:
    # * the GPT extracted ones (call_data)
    # * the Hubspot returned (there can be a lot of metadata, even repeated values)
    # * (this) the set we want to show to our users - what was inserted into Hubspot which was generated by GPT
    # Admittedly, this is quite messy. After hacking it together quickly, I wanted to have a first pass on a more
    # general "fill any form" use-case.
    return HubspotDataEntry(
        transcript=text,
        state=state,
        contact=HubspotObject.from_api_response_props(
            hub_id, ObjectType.CONTACT, contact_form, contact_response.get_props_if_ok()
        ),
        call=HubspotObject.from_api_response_props(
            hub_id, ObjectType.CALL, call_form, call_response.get_props_if_ok()
        ),
        task=HubspotObject.from_api_response_props(
            hub_id, ObjectType.TASK, hs_task_form, hs_task_response.get_props_if_ok()
        ),
        contact_to_call_result=contact_to_call_result,
        contact_to_task_result=contact_to_task_result,
        # TODO(P2, devx): This feels more like a new FormObject
        gpt_contact=HubspotObject.from_api_response_props(
            hub_id, ObjectType.CONTACT, contact_form, contact_form_data.to_dict()
        ),
        gpt_call=HubspotObject.from_api_response_props(
            hub_id, ObjectType.CALL, call_form, call_form_data.to_dict()
        ),
        gpt_task=HubspotObject.from_api_response_props(
            hub_id, ObjectType.TASK, hs_task_form, hs_task_data.to_dict()
        ),
    )


test_data1 = """
I had a chat with Lucas Meyer, who's originally from a small town in Switzerland. 
It's funny because he went to an international boarding school in Geneva, 
and later transferred to a public high school in Zurich. He played a lot of tennis with my friend Michael, 
which we laughed about when we realized the connection. Lucas is super sociable and outgoing. 
He studied economics at Heidelberg University because he was really into understanding how societies work. 
He mentioned he was initially very active in political clubs, but eventually shifted his focus to tech and startups.

During his time at university, he worked part-time for a consulting firm in Berlin, 
where he helped connect German-speaking professionals living abroad with local opportunities. 
That’s how he first crossed paths with my colleague, Julia, through a networking event. 
During his second year, Lucas was introduced to Stefan, 
a CEO who was impressed with Lucas' confidence in reaching out to new people. 
Lucas shared that he studied abroad for a year in Canada, where he played tennis and was the team captain. 
He recalled how his coach would get on his case for being too intense on the court, 
which reminded him of his strict tennis upbringing back home.

Lucas is currently staying in the city for a few more weeks and asked about staying at our place through VRBO 
from October 12th to 19th. I should send him the details so we can coordinate. 
He mentioned he’s previously stayed in a few different Airbnb locations in other neighborhoods with a colleague. 
Stefan, who works as an account executive, 
also mentioned that they’ve had some struggles updating their CRM system regularly, 
which makes it hard to keep the team in sync. Lucas said they usually just have a quick call to update each other, 
but it’s not properly tracked. 
I suggested using a voice memo system to capture updates and feed it into their CRM automatically, 
which Lucas thought would help a lot since even his excellent memory is starting to reach its limits.

Later, Lucas gave me a demo of a software tool they’ve been working on. He was really good at explaining everything,
 but when I complimented his demo skills, he said, "In a real demo, 
 I'd start with more discovery questions to understand your needs first." 
 I thought that was a smart approach and a great learning moment about sales techniques.
"""

if __name__ == "__main__":
    with connect_to_postgres(POSTGRES_LOGIN_URL_FROM_ENV):
        TEST_ORG_NAME = "testing locally"
        test_acc = Account.get_or_onboard_for_email(
            "petherz+localtest@gmail.com", utm_source="test"
        )

        fixture_exists = BaseOrganization.get_or_none(
            BaseOrganization.name == TEST_ORG_NAME
        )
        if bool(fixture_exists):
            organization_id = fixture_exists.id
            test_pipeline = Pipeline.get(Pipeline.organization_id == organization_id)
            print(f"reusing testing fixture for organization {organization_id}")
        else:
            test_org = Organization.get_or_create_for_account_id(
                test_acc.id, name=TEST_ORG_NAME
            )
            test_pipeline = Pipeline.get_or_create_for(
                external_org_id="external_org_id",
                organization_id=test_org.id,
                destination_id=DESTINATION_HUBSPOT_ID,
            )
            if test_pipeline.oauth_data_id is None:
                test_pipeline.oauth_data_id = OauthData.insert(
                    token_type=OAUTH_DATA_TOKEN_TYPE_OAUTH
                ).execute()
                test_pipeline.save()
        # refresh_token must come from prod, as for HubSpot oauth to work with localhost we would need have a full
        # local setup.
        OauthData.update_safely(
            oauth_data_id=test_pipeline.oauth_data_id,
            refresh_token="9ce60291-2261-48a5-8ddb-e26c9bf59845",  # TestApp - hardcoded each time
        )

        test_hs_client = HubspotClient(test_pipeline.oauth_data_id)
        # We put this into a `try` block as it's optional to go through
        owners_response = None
        try:
            owners_response = test_hs_client.list_owners()
            Account.get_or_onboard_for_hubspot(owners_response)
            org_meta = test_hs_client.get_hubspot_account_metadata()
            test_pipeline.external_org_id = str(org_meta.hub_id)
            test_pipeline.save()
            test_org.name = org_meta.hub_domain
            test_org.save()
        except Exception as e:
            print(
                f"WARNING: Cannot get or onboard owners cause {e}, response: {owners_response}"
            )


        test_gpt_client = open_ai_client_with_db_cache()
        test_data_entry_id = BaseDataEntry.insert(
            account_id=test_acc.id,
            display_name=f"Data entry for {test_acc.id}",
            idempotency_id=str(time.time()),
            input_type="test",
        ).execute()

        db_task = Task.create_task("test", test_data_entry_id)
        peter_voxana_user_id = 550982168
        hs_data_entry = extract_and_sync_contact_with_follow_up(
            test_hs_client,
            test_gpt_client,
            text=test_data1,
            db_task=db_task,
            hub_id=test_pipeline.external_org_id,
            hubspot_owner_id=peter_voxana_user_id,
            local_hack=True,
        )

        from app.emails import send_hubspot_result

        send_hubspot_result(
            account_id=test_acc.id,
            idempotency_id_prefix=str(time.time()),
            data=hs_data_entry,
        )

        EmailLog.save_last_email_log_to("result-hubspot-dump.html")
