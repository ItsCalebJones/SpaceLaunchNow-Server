import json

from google.oauth2 import service_account
from pyfcm import FCMNotification

from spacelaunchnow import settings


class NotificationService:
    def __init__(self, debug=settings.DEBUG):
        self.DEBUG = debug

        gcp_json_credentials_dict = json.loads(settings.FCM_CREDENTIALS)
        credentials = service_account.Credentials.from_service_account_info(
            gcp_json_credentials_dict, scopes=["https://www.googleapis.com/auth/firebase.messaging"]
        )
        self.fcm = FCMNotification(
            service_account_file=None, credentials=credentials, project_id=settings.FCM_PROJECT_ID
        )
