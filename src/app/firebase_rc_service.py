import json
import logging

import requests
from django.conf import settings
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


def _get_credentials():
    if not settings.FCM_CREDENTIALS or not settings.FCM_PROJECT_ID:
        logger.warning("Firebase credentials not configured. Remote Config sync disabled.")
        return None

    cred_dict = json.loads(settings.FCM_CREDENTIALS)
    creds = service_account.Credentials.from_service_account_info(
        cred_dict, scopes=["https://www.googleapis.com/auth/firebase.remoteconfig"]
    )
    creds.refresh(GoogleAuthRequest())
    return creds


def update_pinned_content(json_value: str) -> bool:
    """
    Update the 'pinned_content' parameter in Firebase Remote Config.

    Args:
        json_value: JSON string representing the pinned content configuration.

    Returns:
        True if the update was successful, False otherwise.
    """
    creds = _get_credentials()
    if creds is None:
        return False

    project_id = settings.FCM_PROJECT_ID
    base_url = f"https://firebaseremoteconfig.googleapis.com/v1/projects/{project_id}/remoteConfig"

    try:
        # GET current template
        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Accept-Encoding": "gzip",
        }
        resp = requests.get(base_url, headers=headers)
        resp.raise_for_status()
        etag = resp.headers.get("ETag")
        template = resp.json()

        # Ensure parameters dict exists
        if "parameters" not in template:
            template["parameters"] = {}

        # Set or update the pinned_content parameter
        template["parameters"]["pinned_content"] = {
            "defaultValue": {"value": json_value},
            "description": "Pinned content configuration for the app home screen.",
        }

        # PUT updated template
        put_headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json; UTF8",
            "Accept-Encoding": "gzip",
            "If-Match": etag,
        }
        resp = requests.put(base_url, headers=put_headers, json=template)
        resp.raise_for_status()
        logger.info("Successfully updated Firebase Remote Config pinned_content parameter.")
        return True
    except Exception:
        logger.exception("Failed to update Firebase Remote Config.")
        return False
