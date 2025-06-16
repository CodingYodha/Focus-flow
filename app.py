# File: app.py

import streamlit as st
import pandas as pd
import cv2
from fer import FER
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import datetime as dt
import pytz

# Import our custom modules
from ai_coach import get_coach_advice
from google_calendar_agent import get_calendar_service, get_events_in_range

st.set_page_config(layout="wide", page_title="FocusFlow Co-Pilot")

st.title("🚀 FocusFlow Co-Pilot")
st.write("Your autonomous AI agent for productivity and wellness. First, run the schedulers in your terminal, then use this dashboard.")

# --- EDITED FOR INDIAN TIMEZONE ---
INDIAN_TIMEZONE = pytz.timezone('Asia/Kolkata')

# --- Session State Initialization ---
if "emotion" not in st.session_state:
    st.session_state.emotion = "neutral"

# --- Emotion Detection Video Transformer ---
class EmotionTransformer(VideoTransformerBase):
    def __init__(self):
        self.fer_detector = FER(mtcnn=True)
        self.dominant_emotion = "neutral"

    def transform(self, frame):
        img_rgb = frame.to_ndarray(format="bgr24")
        
        # The FER library returns a list of detected faces
        detected_faces = self.fer_detector.detect_emotions(img_rgb)
        
        if detected_faces:
            # Select the first detected face
            bounding_box = detected_faces[0]["box"]
            emotions = detected_faces[0]["emotions"]
            
            # Find the dominant emotion
            self.dominant_emotion = max(emotions, key=emotions.get)
            
            # Draw rectangle and text on the frame
            x, y, w, h = bounding_box
            cv2.rectangle(img_rgb, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img_rgb, f"Emotion: {self.dominant_emotion}", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        return img_rgb

# --- Main App Columns ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("😊 Emotional Check-in")
    st.write("Activate your webcam for a moment so the AI coach can understand your emotional state.")
    
    ctx = webrtc_streamer(
        key="emotion-check", 
        video_transformer_factory=EmotionTransformer,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]} # STUN server for WebRTC
    )

    if ctx.video_transformer:
        st.session_state.emotion = ctx.video_transformer.dominant_emotion
        st.write(f"**Current Detected Emotion:** {st.session_state.emotion.capitalize()}")

with col2:
    st.header("🗓️ Your Day at a Glance")
    
    # This button fetches calendar data and gets advice
    if st.button("Sync Calendar & Get Coach's Tip", type="primary"):
        with st.spinner("Connecting to Google Calendar and consulting the AI coach..."):
            service = get_calendar_service()
            if service:
                now_ist = dt.datetime.now(INDIAN_TIMEZONE)
                # Get events for the next 24 hours
                events = get_events_in_range(service, now_ist, now_ist + dt.timedelta(days=1))
                
                if not events:
                    st.write("No upcoming events found in your calendar for the next 24 hours.")
                    schedule_summary = "Your schedule is clear for today!"
                else:
                    event_list = []
                    for event in events:
                        start_str = event['start'].get('dateTime', event['start'].get('date'))
                        start_dt = dt.datetime.fromisoformat(start_str).astimezone(INDIAN_TIMEZONE)
                        event_list.append({
                            "Task": event['summary'],
                            "Time": start_dt.astimezone().strftime('%I:%M %p')
                        })
                    
                    schedule_df = pd.DataFrame(event_list)
                    st.dataframe(schedule_df, use_container_width=True, hide_index=True)
                    schedule_summary = schedule_df.to_string()

                # Get the AI coach's advice
                advice = get_coach_advice(schedule_summary, st.session_state.emotion)
                st.subheader("💡 Coach's Tip for You")
                st.markdown(f"> {advice}")
            else:
                st.error("Failed to connect to Google Calendar.")

st.markdown("---")
st.info("""
**How to Use This Project:**
1.  **Run the Scheduler:** Open a terminal and run `python autonomous_scheduler.py`. This will populate your Google Calendar. **You only need to do this once.**
2.  **Run the Guardian:** In a *second* terminal, run `python reel_stopper_agent.py`. This will run continuously in the background to watch for distractions.
3.  **Use the Dashboard:** Interact with this web app to perform your emotional check-in and get daily advice.
""")