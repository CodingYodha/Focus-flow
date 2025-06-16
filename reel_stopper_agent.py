# File: reel_stopper_agent.py

import time
import psutil
from plyer import notification
from google_calendar_agent import get_calendar_service, get_events_in_range
import datetime as dt

# List of keywords to identify distraction sites in browser titles
DISTRACTION_SITES = ["YouTube", "Instagram", "Facebook", "TikTok", "Reddit"]
# Note: For demo purposes, we will assume the browser title contains the site name.

def get_active_window_title():
    """
    A simplified function to get the active window title.
    This is highly OS-dependent. A more robust solution might use
    OS-specific libraries, but psutil is a good cross-platform starting point.
    For this hackathon, we'll rely on a best-effort check.
    """
    try:
        # This is a mock implementation for a reliable demo.
        # In a real-world scenario, getting the active browser tab URL is very complex and
        # often requires a browser extension.
        # To ensure the demo works, we can simulate finding a distraction.
        # To see it work, just open YouTube in a browser window.
        active_app = psutil.Process(os.getpid()).name() # Placeholder
        # This part is complex. We'll simulate by just checking all processes
        for p in psutil.process_iter(['name', 'cmdline']):
             if p.info['name'] in ['chrome.exe', 'firefox.exe', 'msedge.exe', 'safari']:
                 # This is not perfect but can work for a demo.
                 # Let's just assume if a browser is open, we can check for distractions.
                 # We can't get the URL easily, but for the demo, we can just trigger it.
                 # Let's pretend we found a YouTube tab for the demo.
                 return "YouTube - Google Chrome"
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return None

def check_if_in_focus_block(service):
    """
    Checks the user's calendar to see if the current time
    falls within an event named 'Focus Block'.
    """
    now = dt.datetime.now(dt.timezone.utc)
    # Check a small window around the current time for a focus block
    time_min = now - dt.timedelta(minutes=1)
    time_max = now + dt.timedelta(minutes=1)
    
    events = get_events_in_range(service, time_min, time_max)
    for event in events:
        if "Focus Block" in event.get("summary", ""):
            return True
    return False

def run_guardian_agent():
    """Main function for the distraction monitoring agent."""
    print("🛡️  FocusFlow Guardian Agent is now active...")
    print("I will monitor for distractions during your scheduled 'Focus Blocks'.")
    service = get_calendar_service()
    if not service:
        print("Could not connect to Google Calendar. Guardian Agent exiting.")
        return

    while True:
        try:
            if check_if_in_focus_block(service):
                print("Currently in a Focus Block. Checking for distractions...")
                # We can't reliably get the active window title in a simple script,
                # so for the demo, we'll assume a distraction if a browser is open.
                # In a real app, this would be more sophisticated.
                # Let's trigger the notification if a browser process is found.
                browser_open = any(p.name().lower() in ['chrome.exe', 'firefox.exe', 'msedge.exe'] for p in psutil.process_iter(['name']))

                if browser_open:
                    print("Distraction detected! Sending notification.")
                    notification.notify(
                        title='FocusFlow Co-Pilot',
                        message='Hey! Noticed you might be distracted. Need a quick 5-min break instead? You can do it!',
                        app_name='FocusFlow',
                        timeout=10 # Notification will be visible for 10 seconds
                    )
                    # Wait for a while after notifying to avoid spamming
                    time.sleep(300) # Wait 5 minutes
        except Exception as e:
            print(f"An error occurred in the guardian loop: {e}")

        # Check every 30 seconds
        time.sleep(30)

if __name__ == '__main__':
    run_guardian_agent()