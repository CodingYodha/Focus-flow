# File: autonomous_scheduler.py

import datetime as dt
import pytz
from google_calendar_agent import get_calendar_service, get_events_in_range, create_calendar_event

# --- Configuration ---
FOCUS_BLOCK_MINUTES = 50
BREAK_BLOCK_MINUTES = 10
BLOCKS_BEFORE_BREAK = 2
SCHEDULING_WINDOW_DAYS = 5
MIN_FREE_SLOT_MINUTES = 60

INDIAN_TIMEZONE = pytz.timezone('Asia/Kolkata')

def robust_datetime_parser(datetime_str):
    """
    A more robust parser that can handle ISO strings ending with 'Z'.
    *** THIS IS THE NEW FUNCTION THAT FIXES THE BUG ***
    """
    # If the string ends with 'Z', replace it with the UTC offset '+00:00'
    # which fromisoformat() can understand.
    if datetime_str.endswith('Z'):
        datetime_str = datetime_str[:-1] + '+00:00'
    return dt.datetime.fromisoformat(datetime_str)

def find_free_slots(existing_events, start_time, end_time):
    """
    Analyzes a list of existing events and returns a list of free time slots.
    """
    free_slots = []
    current_time = start_time
    
    sorted_events = sorted(existing_events, key=lambda x: x['start'].get('dateTime', x['start'].get('date')))

    for event in sorted_events:
        event_start_str = event['start'].get('dateTime')
        if not event_start_str:
            continue
        
        # --- EDITED TO USE THE ROBUST PARSER ---
        # Convert event time using our new robust function, then make it timezone-aware for IST
        event_start = robust_datetime_parser(event_start_str).astimezone(INDIAN_TIMEZONE)
        
        if current_time < event_start:
            free_slots.append({'start': current_time, 'end': event_start})
            
        event_end_str = event['end'].get('dateTime')
        
        # --- EDITED TO USE THE ROBUST PARSER ---
        # Also apply the robust parser to the end time
        current_time = robust_datetime_parser(event_end_str).astimezone(INDIAN_TIMEZONE)

    if current_time < end_time:
        free_slots.append({'start': current_time, 'end': end_time})
        
    return free_slots

def schedule_focus_sessions_in_slots(service, free_slots):
    """
    Takes a list of free slots and fills them with Focus and Break blocks.
    """
    for slot in free_slots:
        slot_duration = (slot['end'] - slot['start']).total_seconds() / 60
        
        if slot_duration >= MIN_FREE_SLOT_MINUTES:
            print(f"\nFound a free slot of {int(slot_duration)} minutes. Scheduling...")
            
            current_time_in_slot = slot['start']
            work_blocks_done = 0
            
            while current_time_in_slot + dt.timedelta(minutes=FOCUS_BLOCK_MINUTES) <= slot['end']:
                if work_blocks_done >= BLOCKS_BEFORE_BREAK:
                    break_start = current_time_in_slot
                    break_end = break_start + dt.timedelta(minutes=BREAK_BLOCK_MINUTES)
                    if break_end <= slot['end']:
                        create_calendar_event(service, "🧠 Mindful Break", break_start, break_end, color_id='2')
                        current_time_in_slot = break_end
                        work_blocks_done = 0
                    else:
                        break
                
                focus_start = current_time_in_slot
                focus_end = focus_start + dt.timedelta(minutes=FOCUS_BLOCK_MINUTES)
                if focus_end <= slot['end']:
                    create_calendar_event(service, "🚀 Focus Block", focus_start, focus_end, color_id='9')
                    current_time_in_slot = focus_end
                    work_blocks_done += 1
                else:
                    break

def run_autonomous_scheduler():
    """Main function to execute the scheduling agent."""
    print("🚀 Starting FocusFlow Autonomous Scheduler...")
    service = get_calendar_service()
    if not service:
        print("Could not connect to Google Calendar. Exiting.")
        return

    now = dt.datetime.now(INDIAN_TIMEZONE)
    start_of_window = now
    end_of_window = now + dt.timedelta(days=SCHEDULING_WINDOW_DAYS)
    
    print(f"Fetching existing events from {start_of_window.strftime('%Y-%m-%d')} to {end_of_window.strftime('%Y-%m-%d')}...")
    existing_events = get_events_in_range(service, start_of_window, end_of_window)
    
    print("Analyzing your calendar to find free time...")
    free_slots = find_free_slots(existing_events, start_of_window, end_of_window)
    
    if not free_slots:
        print("No free slots found to schedule focus sessions.")
        return
        
    print("Scheduling new Focus and Break blocks into your calendar...")
    schedule_focus_sessions_in_slots(service, free_slots)
    
    print("\n✅ Your calendar has been optimized by FocusFlow Co-Pilot!")

if __name__ == '__main__':
    run_autonomous_scheduler()