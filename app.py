# File: app.py

import streamlit as st
import pandas as pd # Still useful for leaderboards
import os
import time

# Import our custom V2 modules
from database import *
from agentic_ai import get_gemini_model_with_function_calling, process_user_request
import google.generativeai as genai

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="FocusFlow V2.1")

# --- Initialize Session State ---
# Ensures that our variables persist across user interactions
if "user_id" not in st.session_state:
    st.session_state.user_id = "demo_user_123" # Use a unique ID for the demo
if "profile" not in st.session_state:
    st.session_state.profile = get_user_profile(st.session_state.user_id)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "gemini_model" not in st.session_state:
    st.session_state.gemini_model = get_gemini_model_with_function_calling()

# --- Onboarding / Profile Setup ---
# This part remains the same. It runs only if no profile is found.
if not st.session_state.profile:
    st.title("Welcome to FocusFlow V2.1!")
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
            st.success("Profile saved! The page will now reload.")
            time.sleep(2) # Give user time to see the message
            st.rerun()
else:
    # --- Main Application Dashboard ---
    # The sidebar setup remains the same
    st.sidebar.title(f"Welcome back, {st.session_state.profile['name']}!")
    stats = get_gamification_stats(st.session_state.user_id)
    if stats:
        st.sidebar.subheader("Your Stats")
        st.sidebar.metric("Level", stats['level'])
        st.sidebar.metric("Points", stats['points'])
        points_in_level = stats['points'] % 500
        st.sidebar.progress(points_in_level / 500, text=f"{points_in_level}/500 Points to next level")
    st.sidebar.subheader("Friend Leaderboard (Demo)")
    leaderboard_data = {"Name": [st.session_state.profile['name'], "Alex", "Brenda"], "Level": [stats['level'] if stats else 1, 12, 10]}
    st.sidebar.dataframe(leaderboard_data, hide_index=True)

    # --- Main Page Layout ---
    st.title("FocusFlow V2.1: Your Sentient Study Partner")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🤖 Agentic Assistant")
        st.write("Record a voice memo on your phone/computer, then upload it here.")

        # +++ THIS IS THE NEW, ROBUST AUDIO UPLOADER +++
        uploaded_audio_file = st.file_uploader(
            "Upload your voice command", 
            type=['wav', 'mp3', 'm4a', 'ogg'],
            label_visibility="collapsed"
        )
        
        if uploaded_audio_file is not None:
            st.audio(uploaded_audio_file, format='audio/wav') # Display the uploaded audio
            
            # Process the uploaded file
            with st.spinner("Assistant is analyzing your audio..."):
                # Configure the API key for this usage
                try:
                    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                except Exception as e:
                    st.error(f"API Key Error: {e}")

                # Use Gemini 1.5 Flash to transcribe the audio
                audio_file = genai.upload_file(uploaded_audio_file)
                transcribe_model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                
                # Ask the model to transcribe the audio
                response = transcribe_model.generate_content(["Please transcribe this audio.", audio_file])
                
                if response and response.text:
                    user_prompt = response.text
                    st.info(f"**You said:** {user_prompt}")

                    # Now, process the transcribed text with our agentic model
                    ai_response, history = process_user_request(st.session_state.gemini_model, user_prompt, st.session_state.chat_history)
                    st.session_state.chat_history = history # Update the chat history
                else:
                    st.error("Sorry, I couldn't understand the audio. Please try again.")

        # Display Chat History (no changes here)
        st.write("---")
        st.subheader("Conversation History")
        if not st.session_state.chat_history:
            st.info("Your conversation will appear here.")
        for message in reversed(st.session_state.chat_history):
            role = "AI" if message.role == "model" else "You"
            with st.chat_message(role):
                st.markdown(message.parts[0].text)

    # --- Column 2 for Quests and Focus Mode (No changes here) ---
    with col2:
        st.header("🎯 Daily Quests & Focus Mode")
        st.subheader("Today's Quests")
        daily_tasks = ["Review CS101 notes", "Complete Math P-Set", "Read one chapter of History"]
        for task in daily_tasks:
            task_key = f"task_{task}_completed"
            is_completed = st.checkbox(task, key=task_key, value=st.session_state.get(task_key, False))
            
            if is_completed and not st.session_state.get(f"points_awarded_for_{task}", False):
                level_up_msg = update_gamification_stats(st.session_state.user_id, points_to_add=50)
                st.session_state[f"points_awarded_for_{task}"] = True
                if level_up_msg: st.toast(level_up_msg, icon="🎉")
                st.rerun() # Rerun to update stats immediately
        
        st.subheader("Guardian Focus Mode")
        focus_duration = st.slider("Select Focus Duration (minutes):", 1, 60, 25)
        
        if st.button("Start Focus Session", type="primary"):
            st.info(f"Focus session started! Avoid distractions for {focus_duration} minutes to earn bonus points.")
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep((focus_duration * 60) / 100) # Sleep for a fraction of the total time
                progress_bar.progress(i + 1)
            
            st.success("Focus Session Complete! Well done!")
            level_up_msg = update_gamification_stats(st.session_state.user_id, points_to_add=100, sessions_to_add=1)
            if level_up_msg: st.toast(level_up_msg, icon="🎉")
            st.balloons()