# File: app.py

import streamlit as st
from streamlit_audiorecorder import audiorecorder
import google.generativeai as genai
import os
import time

# Import our custom V2 modules
from database import *
from agentic_ai import get_gemini_model_with_function_calling, process_user_request

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="FocusFlow V2")

# --- Initialize Session State ---
if "user_id" not in st.session_state:
    st.session_state.user_id = "demo_user" # Hardcoded for the demo
if "profile" not in st.session_state:
    st.session_state.profile = get_user_profile(st.session_state.user_id)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "gemini_model" not in st.session_state:
    st.session_state.gemini_model = get_gemini_model_with_function_calling()

# --- Onboarding / Profile Setup ---
if not st.session_state.profile:
    st.title("Welcome to FocusFlow V2!")
    st.write("Let's set up your profile to personalize your experience.")
    with st.form("profile_form"):
        name = st.text_input("What's your name?")
        user_type = st.selectbox("Are you a school or college student?", ["School", "College"])
        in_time_str = st.time_input("What time do you go to your institution?").strftime("%H:%M")
        out_time_str = st.time_input("What time do you get back?").strftime("%H:%M")
        
        submitted = st.form_submit_button("Save Profile")
        if submitted:
            profile_data = {
                "name": name, "user_type": user_type,
                "in_time": in_time_str, "out_time": out_time_str
            }
            save_user_profile(st.session_state.user_id, profile_data)
            init_gamification_stats(st.session_state.user_id)
            st.session_state.profile = profile_data
            st.success("Profile saved! Please refresh the page.")
            st.rerun()
else:
    # --- Main Application Dashboard ---
    st.sidebar.title(f"Welcome back, {st.session_state.profile['name']}!")
    
    # --- Gamification Dashboard in Sidebar ---
    stats = get_gamification_stats(st.session_state.user_id)
    if stats:
        st.sidebar.subheader("Your Stats")
        st.sidebar.metric("Level", stats['level'])
        st.sidebar.metric("Points", stats['points'])
        
        # Simple progress bar for leveling up
        points_in_level = stats['points'] % 500
        st.sidebar.progress(points_in_level / 500, text=f"{points_in_level}/500 Points to next level")

    # --- Social Leaderboard ---
    st.sidebar.subheader("Friend Leaderboard")
    # For a hackathon, we can use mock data to show the concept
    leaderboard_data = {
        "Name": [st.session_state.profile['name'], "Alex", "Brenda"],
        "Level": [stats['level'], 12, 10]
    }
    st.sidebar.dataframe(leaderboard_data, hide_index=True)
    
    # --- Main Page Layout ---
    st.title("FocusFlow V2: Your Sentient Study Partner")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🤖 Agentic Assistant")
        st.write("Talk to your AI assistant. Ask it to schedule tasks, tell you your plan, or just chat.")

        # --- Real-time Voice & Chat Interface ---
        audio_bytes = audiorecorder("Click to talk to your assistant", "Recording...")
        if audio_bytes:
            # Save audio and transcribe with Gemini
            with st.spinner("Transcribing your voice..."):
                audio_file_path = "temp_audio.wav"
                with open(audio_file_path, "wb") as f:
                    f.write(audio_bytes)
                
                # Use Gemini-1.5-pro for audio transcription (or a local model)
                your_file = genai.upload_file(path=audio_file_path)
                prompt = "Transcribe this audio recording."
                model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
                response = model.generate_content([prompt, your_file])
                user_prompt = response.text
                st.write(f"**You said:** {user_prompt}")

                # Process the transcribed text with our agent
                with st.spinner("Assistant is thinking..."):
                    ai_response, history = process_user_request(st.session_state.gemini_model, user_prompt, st.session_state.chat_history)
                    st.session_state.chat_history = history

        # Display Chat History
        for message in reversed(st.session_state.chat_history):
             role = "AI" if message.role == "model" else "You"
             with st.chat_message(role):
                 st.markdown(message.parts[0].text)

    with col2:
        st.header("🎯 Daily Quests & Focus Mode")
        
        # --- Daily Task Checklist ---
        st.subheader("Today's Quests")
        # Mock daily tasks for the demo
        daily_tasks = ["Review CS101 notes", "Complete Math P-Set", "Read one chapter of History"]
        for task in daily_tasks:
            is_completed = st.checkbox(task, key=f"task_{task}")
            if is_completed:
                # This logic should be more robust to not award points on every rerun
                # Using a flag in session_state is one way
                if f"task_{task}_done" not in st.session_state:
                    level_up_msg = update_gamification_stats(st.session_state.user_id, points_to_add=50)
                    st.session_state[f"task_{task}_done"] = True
                    if level_up_msg: st.toast(level_up_msg)
        
        st.subheader("Guardian Focus Mode")
        focus_duration = st.slider("Select Focus Duration (minutes):", 1, 60, 25)
        
        if st.button("Start Focus Session", type="primary"):
            st.success(f"Focus session started for {focus_duration} minutes! Avoid distractions to earn bonus points.")
            
            # This is where the improved guardian logic would run
            # It's hard to run a true background process reliably from Streamlit Cloud
            # For a hackathon demo, we simulate it:
            with st.spinner(f"Running focus session... You have {focus_duration} minutes."):
                time.sleep(focus_duration * 1) # Use a shorter sleep for the demo, e.g., *1 for seconds
            
            st.success("Focus Session Complete!")
            level_up_msg = update_gamification_stats(st.session_state.user_id, points_to_add=100, sessions_to_add=1)
            if level_up_msg: st.toast(level_up_msg)
            st.balloons()