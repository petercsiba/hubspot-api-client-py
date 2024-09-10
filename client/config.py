import os

ADMIN_CONSOLE_HUBSPOT_REFRESH_TOKEN = os.environ.get(
    "ADMIN_CONSOLE_HUBSPOT_REFRESH_TOKEN"
)
HUBSPOT_APP_ID = "2150554"
HUBSPOT_CLIENT_ID = "501ffe58-5d49-47ff-b41f-627fccc28715"
HUBSPOT_CLIENT_SECRET = os.environ.get("HUBSPOT_CLIENT_SECRET")
# Your RestAPI endpoint, see auth.py::handle_get_request_for_hubspot_oauth_redirect for more details
HUBSPOT_REDIRECT_URL = "https://api.<your domain>/hubspot/oauth/redirect"

OAUTH_DATA_TOKEN_TYPE_OAUTH = "oauth"