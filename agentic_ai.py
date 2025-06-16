# File: agentic_ai.py
import google.generativeai as genai
import streamlit as st
import json
from calendar_functions import schedule_event, list_today_events

def get_gemini_model_with_function_calling():
    """Initializes the Gemini model with our defined tools (functions)."""
    # Define the functions that the model can call
    tools = [
        {"name": "schedule_event", "description": "Schedules a new event on the user's calendar.", "parameters": {
            "type": "object",
            "properties": {
                "task_description": {"type": "string", "description": "The name or description of the task. e.g., 'Team meeting'"},
                "date": {"type": "string", "description": "The date for the event in YYYY-MM-DD format."},
                "time": {"type": "string", "description": "The time for the event in HH:MM 24-hour format."}
            }, "required": ["task_description", "date", "time"]}},
        {"name": "list_today_events", "description": "Lists all events for the current day.", "parameters": {}}
    ]

    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Important: Enable function calling in the model initialization
    model = genai.GenerativeModel(model_name="gemini-pro", tools=tools)
    return model

def process_user_request(model, user_prompt, chat_history):
    """
    Sends the user prompt to Gemini, checks if a function call is needed,
    executes the function, and returns the final response.
    """
    # Start a chat session with history
    chat = model.start_chat(history=chat_history)
    response = chat.send_message(user_prompt)
    
    try:
        # Check if the model wants to call a function
        function_call = response.candidates[0].content.parts[0].function_call
        
        if function_call.name:
            # The model wants to call a function
            function_name = function_call.name
            args = {key: value for key, value in function_call.args.items()}
            
            # Find and call the corresponding Python function
            available_functions = {"schedule_event": schedule_event, "list_today_events": list_today_events}
            function_to_call = available_functions[function_name]
            
            # Execute the function with the arguments provided by the model
            function_response = function_to_call(**args)
            
            # Send the function's return value back to the model
            response = chat.send_message(
                part=genai.types.Part(
                    function_response={"name": function_name, "response": {"result": function_response}}
                )
            )
            return response.candidates[0].content.parts[0].text, chat.history

    except (ValueError, AttributeError):
        # No function call was triggered, just a regular chat response
        return response.candidates[0].content.parts[0].text, chat.history