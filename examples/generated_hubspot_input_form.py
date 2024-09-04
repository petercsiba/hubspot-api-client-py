
HUBSPOT_CONTACT_FIELDS = [
    FieldDefinition(
        name="hubspot_owner_id",
        field_type="number",
        label="Contact owner",
        description=(
            "The owner of a contact. This can be any HubSpot user or Salesforce integration user, "
            "and can be set manually or via Workflows."
        ),
        options=[],
        ignore_in_prompt=True,
        ignore_in_display=True,
        custom_field=False,
    ),
    FieldDefinition(
        name="firstname",
        field_type="text",
        label="First Name",
        description="Contacts first name (not surname)",
        options=[],
        custom_field=False,
    ),
    FieldDefinition(
        name="lastname",
        field_type="text",
        label="Last Name",
        description="Contacts last name (not given name)",
        options=[],
        custom_field=False,
    ),
    FieldDefinition(
        name="jobtitle",
        field_type="text",
        label="Job Title",
        description="A contact's job title",
        options=[],
        custom_field=False,
    ),
    FieldDefinition(
        name="company",
        field_type="text",
        label="Company Name",
        description=(
            "Name of the contact's company. This can be set independently from the name property on "
            "the contact's associated company."
        ),
        options=[],
        custom_field=False,
    ),
    FieldDefinition(
        name="industry",
        field_type="text",
        label="Industry",
        description="The Industry a contact is in",
        options=[],
        custom_field=False,
    ),
    # NOTE: Unclear what are the rules to decide
    # FieldDefinition(
    #     name="lifecyclestage",
    #     field_type="radio",
    #     label="Lifecycle Stage",
    #     description="The qualification of contacts to sales readiness.",
    #     options=[
    #         Option(label="Subscriber", value="subscriber"),
    #         Option(label="Lead", value="lead"),
    #         Option(label="Marketing Qualified Lead", value="marketingqualifiedlead"),
    #         Option(label="Sales Qualified Lead", value="salesqualifiedlead"),
    #         Option(label="Opportunity", value="opportunity"),
    #         Option(label="Customer", value="customer"),
    #         Option(label="Evangelist", value="evangelist"),
    #         Option(label="Other", value="other"),
    #     ],
    #     group_name="contactinformation",
    #     custom_field=False,
    # ),
    # NOTE: Unclear what are the rules to assign
    # FieldDefinition(
    #     name="hs_lead_status",
    #     field_type="radio",
    #     label="Lead Status",
    #     description="The contact's sales, prospecting or outreach status",
    #     options=[
    #         Option(label="New", value="NEW"),
    #         Option(label="Open", value="OPEN"),
    #         Option(label="In Progress", value="IN_PROGRESS"),
    #         Option(label="Open Deal", value="OPEN_DEAL"),
    #         Option(label="Unqualified", value="UNQUALIFIED"),
    #         Option(label="Attempted to Contact", value="ATTEMPTED_TO_CONTACT"),
    #         Option(label="Connected", value="CONNECTED"),
    #         Option(label="Bad Timing", value="BAD_TIMING"),
    #     ],
    #     group_name="sales_properties",
    #     custom_field=False,
    # ),
    FieldDefinition(
        name="email",
        field_type="text",
        label="Email",
        description="A contact's email address",
        options=[],
        custom_field=False,
    ),
    FieldDefinition(
        name="phone",
        field_type="phonenumber",
        label="Phone Number",
        description="A contact's primary phone number",
        options=[],
        custom_field=False,
    ),
    FieldDefinition(
        name="city",
        field_type="text",
        label="City",
        description="A contact's city of residence",
        options=[],
        custom_field=False,
    ),
    FieldDefinition(
        name="state",
        field_type="text",
        label="State/Region",
        description="The contact's state of residence.",
        options=[],
        ignore_in_display=True,
        custom_field=False,
    ),
    FieldDefinition(
        name="country",
        field_type="text",
        label="Country/Region",
        description="The contact's country/region of residence.",
        options=[],
        ignore_in_display=True,
        custom_field=False,
    ),
    FieldDefinition(
        name="hs_object_id",
        field_type="number",
        label="Record ID",
        description=(
            "The unique ID for this record. This value is automatically set by HubSpot and may not be modified."
        ),
        options=[],
        ignore_in_prompt=True,
        custom_field=False,
    ),
]

HUBSPOT_CALL_FIELDS = [
    # "hs_activity_type": FieldDefinition(
    #     name="hs_activity_type",
    #     field_type="select",
    #     label="Call and meeting type",
    #     description="The activity type of the engagement",
    #     options=[],
    #     group_name="engagement",
    #     hubspot_defined=True,
    # ),
    FieldDefinition(
        name="hs_object_id",
        field_type="number",
        label="Record ID",
        description=(
            "The unique ID for this record. This value is automatically set by HubSpot and may not be modified."
        ),
        options=[],
        ignore_in_prompt=True,
        custom_field=False,
    ),
    FieldDefinition(
        name="hubspot_owner_id",
        field_type="number",
        label="Activity assigned to",
        description=(
            "The user that the activity is assigned to in HubSpot. "
            "This can be any HubSpot user or Salesforce integration user, and can be set manually or via Workflows."
        ),
        options=[],
        ignore_in_prompt=True,
        ignore_in_display=True,
        custom_field=False,
    ),
    FieldDefinition(
        name="hs_call_callee_object_id",
        field_type="number",
        label="Callee object id",
        description=(
            "The ID of the HubSpot record associated with the call. "
            "This will be the recipient of the call for OUTBOUND calls, or the dialer of the call for INBOUND calls."
        ),
        options=[],
        ignore_in_prompt=True,
        custom_field=False,
    ),
    FieldDefinition(
        name="hs_call_direction",
        field_type="select",
        label="Call direction",
        description="The direction of the call from the perspective of the HubSpot user.",
        options=[
            Option(label="Inbound", value="INBOUND"),
            Option(label="Outbound", value="OUTBOUND"),
        ],
        custom_field=False,
    ),
    # TODO(P1, fullness): Seems ignored by GPT
    FieldDefinition(
        name="hs_call_disposition",
        field_type="select",
        label="Call outcome",
        description="The outcome of the call",
        options=[
            Option(label="Busy", value="9d9162e7-6cf3-4944-bf63-4dff82258764"),
            Option(label="Connected", value="f240bbac-87c9-4f6e-bf70-924b57d47db"),
            Option(
                label="Left live message", value="a4c4c377-d246-4b32-a13b-75a56a4cd0ff"
            ),
            Option(
                label="Left voicemail", value="b2cf5968-551e-4856-9783-52b3da59a7d0"
            ),
            Option(label="No answer", value="73a0d17f-1163-4015-bdd5-ec830791da20"),
            Option(label="Wrong number", value="17b47fee-58de-441e-a44c-c6300d46f273"),
        ],
        custom_field=False,
    ),
    FieldDefinition(
        name="hs_call_from_number",
        field_type="text",
        label="From number",
        description="The phone number of the person that initiated the call",
        options=[],
        ignore_in_prompt=True,
        custom_field=False,
    ),
    FieldDefinition(
        name="hs_call_status",
        field_type="select",
        label="Call status",
        description="The status of the call",
        options=[
            Option(label="Busy", value="BUSY"),
            Option(label="Calling CRM User", value="CALLING_CRM_USER"),
            Option(label="Canceled", value="CANCELED"),
            Option(label="Completed", value="COMPLETED"),
            Option(label="Connecting", value="CONNECTING"),
            Option(label="Failed", value="FAILED"),
            Option(label="In Progress", value="IN_PROGRESS"),
            Option(label="Missed", value="MISSED"),
            Option(label="No Answer", value="NO_ANSWER"),
            Option(label="Queued", value="QUEUED"),
            Option(label="Ringing", value="RINGING"),
        ],
        custom_field=False,
    ),
    FieldDefinition(
        name="hs_call_title",
        field_type="text",
        label="Call Title",
        description="The title of the call",
        options=[],
        custom_field=False,
    ),
    FieldDefinition(
        name="hs_call_to_number",
        field_type="text",
        label="To Number",
        description="The phone number of the person that was called",
        options=[],
        custom_field=False,
    ),
    FieldDefinition(
        name="hs_timestamp",
        field_type="date",
        label="Activity date",
        description="The date that an engagement occurred",
        options=[],
        custom_field=False,
    ),
    FieldDefinition(
        name="hs_call_body",
        field_type="html",
        label="Call notes",
        description="""
        A concise structured summary of the entire transcript,
        make sure to include all facts, if needed label those facts
        so I can review this in a year and know what happened.
        For better readability, use html paragraphs and bullet points.
        """,
        options=[],
        custom_field=False,
    ),
]

# https://community.hubspot.com/t5/APIs-Integrations/Create-TASK-engagement-with-due-date-and-reminder-via-API/m-p/235759#M14655
HUBSPOT_TASK_FIELDS = [
    FieldDefinition(
        name="hs_object_id",
        field_type="number",
        label="Record ID",
        description=(
            "The unique ID for this record. This value is automatically set by HubSpot and may not be modified."
        ),
        options=[],
        ignore_in_prompt=True,
        custom_field=False,
    ),
    FieldDefinition(
        name="hubspot_owner_id",
        field_type="number",
        label="Assigned to",
        description=(
            "The user that the task is assigned to in HubSpot. "
            "This can be any HubSpot user or Salesforce integration user, and can be set manually or via Workflows."
        ),
        options=[],
        ignore_in_prompt=True,
        ignore_in_display=True,
        custom_field=False,
    ),
    FieldDefinition(
        name="hs_task_subject",
        field_type="text",
        label="Task Title",
        description="The title of the task",
        options=[],
        custom_field=False,
    ),
    FieldDefinition(
        name="hs_task_priority",
        field_type="select",
        label="Priority",
        description="The priority of the task",
        options=[
            Option(label="None", value="NONE"),
            Option(label="Low", value="LOW"),
            Option(label="Medium", value="MEDIUM"),
            Option(label="High", value="HIGH"),
        ],
        custom_field=False,
    ),
    FieldDefinition(
        name="hs_timestamp",
        field_type="date",
        label="Due date",
        description="The due date of the task",
        options=[],
        custom_field=False,
    ),
    # NOTE: The user should set this
    # FieldDefinition(
    #     name="hs_task_status",
    #     field_type="select",
    #     label="Task Status",
    #     description="The status of the task",
    #     options=[
    #         Option(label="Completed", value="COMPLETED"),
    #         Option(label="Deferred", value="DEFERRED"),
    #         Option(label="In Progress", value="IN_PROGRESS"),
    #         Option(label="Not Started", value="NOT_STARTED"),
    #         Option(label="Waiting", value="WAITING"),
    #     ],
    #     group_name="task",
    #     custom_field=False,
    # ),
    # NOTE: Unclear how is this derived
    # FieldDefinition(
    #     name="hs_task_type",
    #     field_type="select",
    #     label="Task Type",
    #     description="The type of the task",
    #     options=[
    #         Option(label="Call", value="CALL"),
    #         Option(label="Email", value="EMAIL"),
    #         Option(label="LinkedIn", value="LINKED_IN"),
    #         Option(label="Meeting", value="MEETING"),
    #         Option(
    #             label="Sales Navigator - Connection Request", value="LINKED_IN_CONNECT"
    #         ),
    #         Option(label="Sales Navigator - InMail", value="LINKED_IN_MESSAGE"),
    #         Option(label="To Do", value="TODO"),
    #     ],
    #     group_name="task",
    #     custom_field=False,
    # ),
    FieldDefinition(
        name="hs_task_body",
        field_type="html",
        label="To Dos",
        description="Action items and follows ups I need to do in concise bullet points ordered by priority top down",
        options=[],
        ignore_in_display=True,  # It's displayed as a separate textarea
        custom_field=False,
    ),
]
