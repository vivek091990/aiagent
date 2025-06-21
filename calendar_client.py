import os
import pickle
import datetime
import pytz
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import Config

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

class CalendarClient:
    def __init__(self):
        self.creds = self._authenticate()
        self.service = build('calendar', 'v3', credentials=self.creds)

    def _authenticate(self):
        creds = None
        if os.path.exists(Config.GOOGLE_TOKEN_PATH):
            with open(Config.GOOGLE_TOKEN_PATH, 'rb') as token_file:
                creds = pickle.load(token_file)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    Config.CREDENTIALS_JSON, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(Config.GOOGLE_TOKEN_PATH, 'wb') as token_file:
                pickle.dump(creds, token_file)
        return creds

    def create_event(self, title: str, start_time: datetime.datetime, duration: int):
        end_time = start_time + datetime.timedelta(minutes=duration)
        event = {
            'summary': title,
            'start': {'dateTime': start_time.isoformat(), 'timeZone': Config.TIMEZONE},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': Config.TIMEZONE}
        }
        created = self.service.events().insert(calendarId='primary', body=event).execute()
        return created.get('htmlLink')
