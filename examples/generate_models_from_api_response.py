# FOR CODE GEN
test_hs_client = HubspotClient(test_pipeline.oauth_data_id)


def _gen_field_from_properties_api_response(response: ModelProperty) -> FieldDefinition:
    return FieldDefinition(
        name=response.name,
        field_type=response.field_type,
        label=response.label,
        description=response.description,
        options=response.options,
        custom_field=response.hubspot_defined
        is False,  # only if non-none and set to False it is a custom field
    )


def _gen_form_from_properties_api_response(
    form_name: FormName,
    field_list: List[ModelProperty],
) -> FormDefinition:
    fields = []
    for field_response in [f for f in field_list if f.name in ALLOWED_FIELDS]:
        field: FieldDefinition = _gen_field_from_properties_api_response(field_response)
        fields.append(field)
    return FormDefinition(form_name, fields)


props = test_hs_client.list_custom_properties(object_type="contact")
contact_def = _gen_form_from_properties_api_response(props.results)
print(f"contact_def to_python_definition: {contact_def.to_python_definition()}")
