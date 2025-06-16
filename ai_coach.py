# File: ai_coach.py

import google.generativeai as genai
import streamlit as st
import pandas as pd

def get_coach_advice(schedule_summary, detected_emotion):
    """
    Uses Google's Gemini Pro model to generate advice based on the user's
    schedule summary and detected emotional state.
    """
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception:
        return "Error: Google API Key not configured. Please add it to your .streamlit/secrets.toml file."

    # The prompt is the most important part. It gives the AI its personality and context.
    prompt = f"""
    You are FocusFlow, an empathetic and insightful AI wellness coach for students.
    Your tone is encouraging, understanding, and never judgmental.

    Here is the user's context:
    - Their visually detected emotion from their webcam is: **{detected_emotion}**
    - Here is a summary of their upcoming scheduled events: 
    {schedule_summary}

    Your Task:
    Write a short, single paragraph of advice that synthesizes BOTH their emotional state and their schedule.
    - **Directly address the detected emotion.** For example, if the emotion is 'sad', start with something like, "I can see you might be feeling a bit down today, and that's completely okay..."
    - **Connect the emotion to the schedule.** If they look 'happy' and have a busy day, you could say, "It's great to see you looking happy and ready to tackle a productive day!" If they look 'stressed' and have a busy day, acknowledge that the schedule might be the cause.
    - **Give one specific, actionable tip.** Don't just give platitudes. If they have back-to-back 'Focus Blocks', suggest a specific type of stretch during their 'Mindful Break'. If they look tired, suggest they use their break to step away from the screen entirely.
    - Keep it concise and positive.
    """

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred with the AI model: {e}"