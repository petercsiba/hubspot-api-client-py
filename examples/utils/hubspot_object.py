
def _get_field(fields: List[FieldDefinition], name: str):
    for field in fields:
        if field.name == name:
            return field

    # This function is oftentimes used to check if name is in the field list so only warning.
    # It's a bit annoying, but can be lifesaving when developing.
    print(f"WARNING: Requested field {name} not in list")
    return None


# This class will act as the value storage
# TODO(P1, devx): This starts to feel like FormData, once HubSpot becomes important again we can think of refactor
#  - would need some custom display transformers for e.g. get_link.
class HubspotObject:
    def __init__(
        self,
        hub_id: Optional[str],
        object_type: ObjectType,
        form: FormDefinition,
    ):
        self.hub_id = None
        try:
            if hub_id is not None:
                self.hub_id = int(hub_id)
        except ValueError as e:
            print(f"WARNING: invalid hub_id {hub_id} given, expected int: {e}")

        self.object_type = object_type
        self.form = form
        self.data = {}  # you can just plug into properties

    @classmethod
    def from_api_response_props(
        cls,
        hub_id: Optional[str],
        object_type: ObjectType,
        form: FormDefinition,
        response_props: Optional[Dict[str, Any]],
    ) -> Optional["HubspotObject"]:
        if response_props is None:
            return None

        # Hubspot response has many more fields than what we care about - so this will end up ignoring a bunch.
        result = HubspotObject(hub_id=hub_id, object_type=object_type, form=form)
        for field_name, value in response_props.items():
            result.set_field_value(field_name, value)
        return result

    def get_field(self, field_name):
        return _get_field(self.form.fields, field_name)

    def set_field_value(self, field_name: str, value: Any, raise_key_error=False):
        field = self.get_field(field_name)
        if bool(field):
            self.data[field_name] = value
        else:
            # print(f"INFO: omitting `{field_name}` from")
            if raise_key_error:
                raise KeyError(
                    f"Field '{field_name}' does not exist on HubspotContact."
                )

    def get_display_value(self, field_name: str) -> str:
        field = self.get_field(field_name)
        if bool(field):
            return field.display_value(self.data.get(field_name))
        return "None"

    def get_field_display_label_with_value(self, field_name: str) -> Tuple[str, Any]:
        value = None
        if field_name == FieldNames.HS_OBJECT_ID.value:
            # TODO(P2, devx): This should be outside of here, but the complexity is getting harder to manage
            link_href = self.get_link()
            if bool(link_href):
                value = f'<a href="{self.get_link()}">{self.get_display_value(field_name)} - See in Hubspot (Web)</a>'

        if value is None:
            value = self.get_display_value(field_name)

        return self.get_field(field_name).label, value

    def get_link(self) -> Optional[str]:
        if self.hub_id is None:
            return None

        object_id = self.get_display_value(FieldNames.HS_OBJECT_ID.value)
        if self.object_type == ObjectType.CONTACT:
            # Task actually cannot be linked - it only really works for contacts.
            return f"https://app.hubspot.com/contacts/{self.hub_id}/record/0-1/{object_id}/view/1"

        # TODO(P2, ux): Once we figure it out we can add it back
        # object_id = self.get_display_value(FieldNames.HS_OBJECT_ID.value)
        # if bool(object_id):
        #     return f"https://app.hubspot.com/contacts/{self.hub_id}/record/{self.object_type.value}/{object_id}/"

        return None


@dataclass
class HubspotDataEntry:
    transcript: str
    state: str = "new"  # "short", "incomplete", "error_gpt", "error_hubspot_sync", "warning_already_created", "success"

    contact: Optional[HubspotObject] = None
    call: Optional[HubspotObject] = None
    task: Optional[HubspotObject] = None
    contact_to_call_result: Dict[str, Any] = None
    contact_to_task_result: Dict[str, Any] = None

    gpt_contact: Optional[HubspotObject] = None
    gpt_call: Optional[HubspotObject] = None
    gpt_task: Optional[HubspotObject] = None

    def contact_name(self):
        if self.contact is not None:
            first_name = self.contact.get_display_value(FieldNames.FIRSTNAME.value)
            last_name = self.contact.get_display_value(FieldNames.LASTNAME.value)
        elif self.gpt_contact is not None:
            first_name = self.gpt_contact.get_display_value(FieldNames.FIRSTNAME.value)
            last_name = self.gpt_contact.get_display_value(FieldNames.LASTNAME.value)
        else:
            first_name = "Unknown"
            last_name = ""
        first_str = str(first_name) if bool(first_name) else ""
        last_str = str(last_name) if bool(last_name) else ""
        return f"{first_str} {last_str}"
