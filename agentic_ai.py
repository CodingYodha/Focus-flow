# File: agentic_ai.py (Corrected for older google-generativeai versions)

import google.generativeai as genai
import streamlit as st
import json

# Import the functions the AI can call
from calendar_functions import schedule_event, list_today_events

# Import the necessary components from the library to build the schema correctly
# 'Part' has been removed from this import statement.
from google.generativeai.types import FunctionDeclaration, Tool

def get_gemini_model_with_function_calling():
    """Initializes the Gemini model with our defined tools (functions)."""
    
    # This schema definition is correct and does not need to change.
    schedule_event_func = FunctionDeclaration(
        name="schedule_event",
        description="Schedules a new event on the user's Google calendar.",
        parameters={
            "type": "OBJECT",
            "properties": {
                "task_description": {"type": "STRING", "description": "The name or description of the task. e.g., 'Team meeting'"},
                "date": {"type": "STRING", "description": "The date for the event in YYYY-MM-DD format."},
                "time": {"type": "STRING", "description": "The time for the event in HH:MM 24-hour format."}
            },
            "required": ["task_description", "date", "time"]
        },
    )

    list_today_events_func = FunctionDeclaration(
        name="list_today_events",
        description="Lists all events for the current day from the Google calendar.",
        parameters={}
    )

    calendar_tool = Tool(
        function_declarations=[
            schedule_event_func,
            list_today_events_func,
        ],
    )

    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Google API Key not found. Please check your secrets.toml file. Error: {e}")
        return None

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-preview-05-20",
        tools=[calendar_tool]
    )
    return model

def process_user_request(model, user_prompt, chat_history):
    """
    Sends the user prompt to Gemini, checks if a function call is needed,
    executes the function, and returns the final response.
    """
    if model is None:
        return "Error: The AI model is not initialized. Please check your API key.", []

    chat = model.start_chat(history=chat_history)
    
    try:
        response = chat.send_message(user_prompt)
        first_part = response.candidates[0].content.parts[0]
        
        if first_part.function_call.name:
            function_call = first_part.function_call
            function_name = function_call.name
            args = {key: value for key, value in function_call.args.items()}
            
            available_functions = {
                "schedule_event": schedule_event,
                "list_today_events": list_today_events,
            }
            function_to_call = available_functions[function_name]
            
            function_response_str = function_to_call(**args)
            
            # +++ THIS IS THE CORRECTED BLOCK +++
            # Construct the function response dictionary
            function_response_content = {
                "function_response": {
                    "name": function_name,
                    "response": {
                        "result": function_response_str
                    }
                }
            }
            # Send the dictionary directly back to the model without using 'Part'
            response = chat.send_message(content=function_response_content)
            # +++ END OF CORRECTION +++

            final_text = response.candidates[0].content.parts[0].text
            return final_text, chat.history

    except (ValueError, AttributeError, IndexError):
        try:
            final_text = response.candidates[0].content.parts[0].text
            return final_text, chat.history
        except (IndexError, AttributeError):
            return "Sorry, I encountered an issue and couldn't generate a response. Please try again.", chat.history
            
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return f"Sorry, I ran into an unexpected error: {e}", chat.history