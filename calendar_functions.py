# File: calendar_functions.py
import datetime as dt
from google_calendar_agent import get_calendar_service, create_calendar_event, get_events_in_range

def schedule_event(task_description: str, date: str, time: str) -> str:
    """
    Schedules an event on the user's Google Calendar.

    Args:
        task_description (str): What the event is about (e.g., 'Study for Math exam').
        date (str): The date in YYYY-MM-DD format.
        time (str): The time in HH:MM (24-hour) format.
    
    Returns:
        str: A confirmation message that the event was created.
    """
    service = get_calendar_service()
    if not service:
        return "Error: Could not connect to Google Calendar."
    
    try:
        start_time_dt = dt.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        # Assume events are 1 hour long for simplicity
        end_time_dt = start_time_dt + dt.timedelta(hours=1)
        
        create_calendar_event(service, task_description, start_time_dt, end_time_dt, color_id='5') # 5 = Yellow
        return f"Success! I've scheduled '{task_description}' on {date} at {time}."
    except Exception as e:
        return f"Error scheduling event: {e}. Please check the date and time format."

def list_today_events() -> str:
    """
    Lists all events scheduled for today from the user's Google Calendar.

    Returns:
        str: A formatted string of today's events.
    """
    service = get_calendar_service()
    if not service:
        return "Error: Could not connect to Google Calendar."

    now = dt.datetime.now(dt.timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999)
    
    events = get_events_in_range(service, start_of_day, end_of_day)
    
    if not events:
        return "You have no events scheduled for today."
    
    event_list = "Here are your events for today:\n"
    for event in events:
        start_time_str = event['start'].get('dateTime', event['start'].get('date'))
        start_dt = dt.datetime.fromisoformat(start_time_str.replace('Z', '+00:00')).astimezone()
        event_list += f"- {start_dt.strftime('%I:%M %p')}: {event['summary']}\n"
        
    return event_list