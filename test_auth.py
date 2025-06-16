from google_calendar_agent import get_calendar_service
print("Attempting to get calendar service to generate token...")
service = get_calendar_service()
if service:
    print("SUCCESS: token.json has been created or updated.")
else:
    print("ERROR: Could not get calendar service.")