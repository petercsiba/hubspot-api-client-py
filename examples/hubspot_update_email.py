


def _hubspot_obj_to_table(
    heading: str,
    obj: Optional[HubspotObject],
    extra_content: str = "",
) -> str:
    rows = []
    for field in obj.form.fields:
        if field.ignore_in_display or field.ignore_in_email:
            print(
                f"INFO: ignoring {field.name} for emails (ignore_id_display: {field.ignore_in_display}"
                f"ignore_in_email: {field.ignore_in_email}"
            )
            continue
        key, value = obj.get_field_display_label_with_value(field.name)
        rows.append(_format_summary_table_row(key, value))
    rows_html = "\n".join(rows)
    return table_template(
        heading=heading, rows_html=rows_html, extra_content_html=extra_content
    )


def _hubspot_objs_maybe_to_table(
    heading: str,
    obj: Optional[HubspotObject],
    gpt_obj: Optional[HubspotObject],
    extra_content: str = "",
) -> str:
    if obj is None:
        result = main_content_template(
            heading=heading, content="Could not sync data to HubSpot (API error)"
        )
        if gpt_obj is None:
            result = main_content_template(
                heading=heading,
                content="Could not parse data into structure (GPT error)",
            )
        else:
            result += _hubspot_obj_to_table(heading, gpt_obj, extra_content)
    else:
        result = _hubspot_obj_to_table(heading, obj, extra_content)
    return result


def send_hubspot_result(
    account_id: UUID, idempotency_id_prefix: str, data: HubspotDataEntry
) -> bool:
    person_name = data.contact_name()
    idempotency_id_suffix = data.state

    email_params = EmailLog.get_email_reply_params_for_account_id(
        account_id=account_id,
        idempotency_id=f"{idempotency_id_prefix}-result-{idempotency_id_suffix}",
        subject=f"HubSpot Data Entry for {person_name} - {data.state.capitalize()}",
    )
    pre_header = email_params.subject

    if data.state in ["short", "incomplete"]:
        email_params.body_html = simple_email_body_html(
            title=f"Note is {data.state} - please enter more information.",
            sub_title="This is how I understood it",
            content_text=data.transcript,
        )
        return send_email(params=email_params)

    extra_info_map = {
        "error_gpt": "I had problems transforming your note into a HubSpot structures",
        "error_hubspot_sync": "I encountered problems while syncing your data into your HubSpot",
        "warning_already_created": "Note: The contact already exists in your HubSpot",
    }
    extra_info = ""
    if data.state in extra_info_map:
        extra_info_content = extra_info_map[data.state]
        extra_info = main_content_template(
            heading="Sync Status",
            content=extra_info_content,
        )
        pre_header = extra_info_content

    # success / error with partial results
    contact_table = _hubspot_objs_maybe_to_table(
        "Contact Info", data.contact, data.gpt_contact
    )

    # Bit of a hack to restructure rendering of task To Dos
    todos_extra_content = ""
    if bool(data.task):
        todos_field_name = FieldNames.HS_TASK_BODY.value
        if todos_field_name in data.task.data:
            todos_extra_content = """
            <p><b>{heading}</b></p>
            <p>{content}</p>""".format(
                heading="To Dos", content=data.task.get_display_value(todos_field_name)
            )

    task_table = _hubspot_objs_maybe_to_table(
        "Follow up Tasks",
        data.task,
        data.gpt_task,
        todos_extra_content,
    )

    if bool(data.call):
        call_body_value = data.call.get_display_value(FieldNames.HS_CALL_BODY.value)
        further_details = main_content_template(
            heading="Further Details",
            content=f"""<p style = "line-height: 1.5;" >{call_body_value}</p>""",
        )
    else:
        further_details = main_content_template(
            heading="Further Details",
            content="<p>Could not sync data to HubSpot (API error)</p>",
        )

    email_params.body_html = full_template(
        title="HubSpot Data Entry Confirmation",
        pre_header=pre_header,
        content="""
            {contact_table}
            {task_table}
            {further_details}
            {extra_info}
            """.format(
            contact_table=contact_table,
            task_table=task_table,
            further_details=further_details,
            extra_info=extra_info,
        ),
    )
    return send_email(params=email_params)