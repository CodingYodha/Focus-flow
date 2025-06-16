# File: app.py

import streamlit as st
import pandas as pd
import cv2
from fer import FER
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import datetime as dt
import pytz
import time # We'll use this for the polling loop

# Import our custom modules
from ai_coach import get_coach_advice
from google_calendar_agent import get_calendar_service, get_events_in_range

st.set_page_config(layout="wide", page_title="FocusFlow Co-Pilot")

st.title("🚀 FocusFlow Co-Pilot")
st.write("Your autonomous AI agent for productivity and wellness. First, run the schedulers in your terminal, then use this dashboard.")

INDIAN_TIMEZONE = pytz.timezone('Asia/Kolkata')

# --- START: FIX 1 - PRE-LOAD THE HEAVY MODEL ---
# This decorator tells Streamlit to run this function only once and cache the result.
# This prevents the slow FER model from being reloaded on every interaction.
@st.cache_resource
def load_fer_model():
    print("Loading FER model...")
    return FER(mtcnn=True)

# Load the model into a global variable when the app starts.
fer_detector = load_fer_model()
# --- END: FIX 1 ---

def robust_datetime_parser(datetime_str):
    if datetime_str.endswith('Z'):
        return dt.datetime.fromisoformat(datetime_str[:-1] + '+00:00')
    return dt.datetime.fromisoformat(datetime_str)

# --- Session State Initialization ---
if "emotion" not in st.session_state:
    st.session_state.emotion = "neutral"

# --- Emotion Detection Video Transformer ---
class EmotionTransformer(VideoTransformerBase):
    def __init__(self):
        # Now, we just reference the pre-loaded global model. This is instantaneous.
        self.fer_detector = fer_detector
        self.dominant_emotion = "neutral"

    def transform(self, frame):
        img_rgb = frame.to_ndarray(format="bgr24")
        detected_faces = self.fer_detector.detect_emotions(img_rgb)
        
        if detected_faces:
            bounding_box = detected_faces[0]["box"]
            emotions = detected_faces[0]["emotions"]
            self.dominant_emotion = max(emotions, key=emotions.get)
            
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
    
    # --- START: FIX 2 & 3 - IMPROVE CONNECTION SETTINGS ---
    # Define a list of STUN servers for better reliability
    STUN_SERVERS = {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302"]},
        ]
    }
    
    ctx = webrtc_streamer(
        key="emotion-check", 
        video_transformer_factory=EmotionTransformer,
        rtc_configuration=STUN_SERVERS, # Use the list of STUN servers
        async_processing=True,
        # Give the connection up to 30 seconds to initialize, instead of the default 10
        media_stream_constraints={"video": True, "audio": False},
        #async_processing_timeout=30 
    )
    # --- END: FIX 2 & 3 ---

    # This label will now update in real-time.
    emotion_placeholder = st.empty()
    emotion_placeholder.write(f"**Current Detected Emotion:** {st.session_state.emotion.capitalize()}")

    if ctx.state.playing and ctx.video_transformer:
        # Continuously update the emotion
        current_emotion = ctx.video_transformer.dominant_emotion
        if st.session_state.emotion != current_emotion:
            st.session_state.emotion = current_emotion
            emotion_placeholder.write(f"**Current Detected Emotion:** {st.session_state.emotion.capitalize()}")


with col2:
    st.header("🗓️ Your Day at a Glance")
    
    if st.button("Sync Calendar & Get Coach's Tip", type="primary"):
        with st.spinner("Connecting to Google Calendar and consulting the AI coach..."):
            # ... (The rest of your code for this column remains the same)
            service = get_calendar_service()
            if service:
                now_ist = dt.datetime.now(INDIAN_TIMEZONE)
                events = get_events_in_range(service, now_ist, now_ist + dt.timedelta(days=1))
                
                if not events:
                    st.write("No upcoming events found in your calendar for the next 24 hours.")
                    schedule_summary = "Your schedule is clear for today!"
                else:
                    event_list = []
                    for event in events:
                        start_str = event['start'].get('dateTime', event['start'].get('date'))
                        start_dt = robust_datetime_parser(start_str).astimezone(INDIAN_TIMEZONE)
                        event_list.append({
                            "Task": event['summary'],
                            "Time": start_dt.strftime('%I:%M %p')
                        })
                    
                    schedule_df = pd.DataFrame(event_list)
                    st.dataframe(schedule_df, use_container_width=True, hide_index=True)
                    schedule_summary = schedule_df.to_string()

                advice = get_coach_advice(schedule_summary, st.session_state.emotion)
                st.subheader("💡 Coach's Tip for You")
                st.markdown(f"> {advice}")
            else:
                st.error("Failed to connect to Google Calendar.")

st.markdown("---")
st.info("""
**How to Use This Project:**
1.  **Run the Scheduler:** Open a terminal and run `python autonomous_scheduler.py`.
2.  **Run the Guardian:** In a *second* terminal, run `python reel_stopper_agent.py`.
3.  **Use the Dashboard:** Interact with this web app.
""")