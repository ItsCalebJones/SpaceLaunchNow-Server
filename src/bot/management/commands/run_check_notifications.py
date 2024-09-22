import json
import os

from django.core.management.base import BaseCommand
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from spacelaunchnow import settings

# Define the scope for FCM Data API (read-only)
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# Set your project and app IDs
PROJECT_ID = "space-launch-now"
ANDROID_APP_ID = "1:610310574961:android:4553f5c8ecd77279"

# Path to the token file
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = os.path.join(
    settings.BASE_DIR, "client_secret.json"
)  # Downloaded from Google Cloud OAuth2 Credentials


class Command(BaseCommand):
    help = "Fetch FCM delivery data"

    def handle(self, *args, **kwargs):
        # Authenticate and retrieve the delivery data
        self.stdout.write(self.style.SUCCESS("Starting to fetch FCM data..."))
        delivery_data = self.get_delivery_data()
        self.stdout.write(self.style.SUCCESS(json.dumps(delivery_data, indent=4)))

    def authenticate(self):
        """Authenticate using OAuth2 for user-based credentials."""
        creds = None
        # Check if token.json exists and load the credentials
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        # If there are no valid credentials available, ask the user to log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)  # Opens a browser to log in
            # Save the credentials for the next run
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        return creds

    def get_delivery_data(self):
        """Fetch delivery data from FCM Data API."""
        creds = self.authenticate()

        # Now, build the service object for the FCM Data API
        service = build("fcmdata", "v1beta1", credentials=creds)

        # Construct the parent resource path
        parent = f"projects/{PROJECT_ID}/androidApps/{ANDROID_APP_ID}"

        # Make the API call to list delivery data
        request = service.projects().androidApps().deliveryData().list(parent=parent)
        response = request.execute()
        return response
