# File: google_calendar_agent.py

import datetime as dt
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def get_calendar_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def get_events_in_range(service, time_min, time_max):
    """
    Fetches all events from the user's primary calendar within a specified time range.
    *** EDITED TO FIX THE TIMESTAMP BUG ***
    """
    events_result = service.events().list(
        calendarId='primary', 
        timeMin=time_min.isoformat(), # The .isoformat() on a timezone-aware object is already correct. No 'Z' needed.
        timeMax=time_max.isoformat(), # The .isoformat() on a timezone-aware object is already correct. No 'Z' needed.
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    return events_result.get('items', [])

def create_calendar_event(service, summary, start_time, end_time, color_id):
    event = {
        'summary': summary,
        'description': 'Automatically scheduled by FocusFlow Co-Pilot.',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'colorId': color_id
    }
    
    try:
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {created_event.get('summary')} at {start_time.strftime('%Y-%m-%d %H:%M')}")
        return created_event
    except HttpError as error:
        print(f'An error occurred while creating event: {error}')
        return None

# Adding this block so you can test the connection directly if you want
if __name__ == '__main__':
    print("Attempting to connect to Google Calendar to test authentication...")
    service = get_calendar_service()
    if service:
        print("✅ Successfully connected to Google Calendar service.")
    else:
        print("❌ Failed to connect.")