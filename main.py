#Purpose: This is the central control script of your command-line interface (CLI) application.
# It orchestrates the flow, tying together the gemini_parser.py and calendar_manager.py modules.
#Key Functionality:

    #Initializes the application (e.g., loads environment variables).
    #Presents a command-line interface to the user, allowing them to type in requests.
    #Takes the user's natural language input.
    #Passes this input to gemini_parser.py to extract event details.
    #Performs any necessary validation or default-setting on the data received from the parser.
    #Passes the validated event details to calendar_manager.py to create the event.
    #Provides feedback to the user based on the success or failure of the operations (including structured error messages).
    #Manages the main application loop (e.g., continues to ask for input until the user types 'exit').

#Connection: This file imports and uses functions from both gemini_parser.py and calendar_manager.py. It's the "brain" that coordinates the other specialized modules

import json
import datetime as dt
from datetime import timezone
from datetime import datetime
from gemini_parser import GeminiParser
from calender_manager import CalendarManager

def create_event(user_input, gemini_parser, calender_manager):
    #Pass the user input to Gemini
    gemini_response_text = gemini_parser.parse_event_details(user_input)
    
    # Parse the JSON output from gemini
    try:
        parsed_data = json.loads(gemini_response_text)
        print("\nGemini successfully parsed the event details: ")
        print(parsed_data)

    except json.JSONDecodeError:
        print("Error: Gemini's response was not valid")
        print("Raw response:",gemini_response_text)
        return
     
    #Check if this is an availability checks or an event to create.
    if parsed_data.get("request_type") == "availability_check":
        print("\nThis is a request for availability. The functionality is not yet implemented.")
        #You'll build this part later
        return 
    
    # Format the data for the Google Calender API
    # The Google Calender API expects time in ISO 8601 format.    # The JSON from Gemini needs to be converted
    try:
        # Example conversion (assuming Gemini returns "YYYY-MM-DD HH:MM:SS" format)
        # You may need to adjust the format based on your prompt engineering.
        start_time_str = parsed_data.get("start_time")
        end_time_str = parsed_data.get("end_time")

        # Strip the timezone offset from the string
        # This takes a string like "2025-08-16T12:00:00-00:00" and makes it "2025-08-16T12:00:00"
        if start_time_str and len(start_time_str) > 19:
            start_time_str = start_time_str[:-6]
        if end_time_str and len(end_time_str) > 19:
            end_time_str = end_time_str[:-6]

        start_datetime = datetime.datetime.fromisoformat(start_time_str)
        end_datetime = datetime.datetime.fromisoformat(end_time_str)

        # Create the event body in the format the Google Calender API
        event_body = {
            'summary': parsed_data.get('summary'),
            'description': parsed_data.get('description'),
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'America/Chicago',  # Or your local timezone
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/Chicago',
            },
            
        }

        # Conditionally add the recurrence field
        recurrence_rule = parsed_data.get('recurrence')
        if recurrence_rule:
            event_body['recurrence'] = [recurrence_rule]
            print("\nRecurring event detected. Adding recurrence rule to event body.")

        # Pass the event data to the Calender Manger
        print("\nAttempting to create event...")
        created_event = calender_manager.add_event(event_body)

        if created_event:
            print("\n Event Created succesfully!")
            print(f"Event ID: {created_event['id']}")
            print(f"Event URL: {created_event["htmlLink"]}")
    except(KeyError, ValueError) as e:
        print(f"Error: Missing or invalid data for event creation: {e}")
        print("Please ensure Gemini's output contains valid 'summary', 'description', 'start_time', and 'end_time' keys.")
def create_event_1(user_input, gemini_parser, calender_manager):
    """
    Parses user input for event details and creates a corresponding event
    in the calendar. This function is designed to handle multiple events
    from a single string.
    
    Args:
        user_input (str): The structured string containing event details.
        gemini_parser: The parser object (e.g., an instance of EventParser).
        calender_manager: The manager object for interacting with the calendar API.
    """
    # Use the local `parse_event_details` function, not a Gemini model.
    # The `gemini_parser` is now a direct reference to the function you have.
    parsed_events = gemini_parser.parse_event_details(user_input)

    # Check if a single object with "request_type" was returned.
    # This handles the case where the function is still called with
    # a query for availability.
    if len(parsed_events) == 1 and "request_type" in parsed_events[0]:
        if parsed_events[0]["request_type"] == "availability_check":
            print("\nThis is a request for availability. The functionality is not yet implemented.")
            return

    # Loop through each event dictionary in the list returned by the parser.
    print("\nParsing complete. Attempting to create events...")
    for event_data in parsed_events:
        try:
            # Extract data for the current event.
            summary = event_data.get('summary')
            description = event_data.get('description')
            start_time_str = event_data.get("start_time")
            end_time_str = event_data.get("end_time")

            # Check for essential data.
            if not all([summary, start_time_str, end_time_str]):
                print(f"Error: Missing essential data for event: {event_data}. Skipping.")
                continue

            # Convert the ISO 8601 strings to datetime objects.
            # No need for string slicing as the ISO 8601 format is now consistent.
            start_datetime = datetime.datetime.fromisoformat(start_time_str)
            end_datetime = datetime.datetime.fromisoformat(end_time_str)

            # Create the event body for the calendar API.
            event_body = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'America/Chicago',  # Use your local timezone
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/Chicago',
                },
            }

            # Conditionally add the recurrence field.
            recurrence_rule = event_data.get('recurrence')
            if recurrence_rule:
                event_body['recurrence'] = [recurrence_rule]
                print(f"\nRecurring event detected for '{summary}'. Adding recurrence rule.")

            # Pass the event data to the Calendar Manager.
            print(f"Creating event: '{summary}'...")
            created_event = calender_manager.add_event(event_body)

            if created_event:
                print("\nEvent created successfully!")
                print(f"Event ID: {created_event['id']}")
                print(f"Event URL: {created_event['htmlLink']}")
                print("-" * 20)  # Separator for multiple events

        except (KeyError, ValueError, TypeError) as e:
            print(f"Error: Invalid data for event creation. Check the parsed data for {summary}. Error: {e}")
            print("Skipping this event.")
            print("-" * 20)

# The following is a placeholder for your CalenderManager and GeminiParser classes
# to make this code runnable for demonstration.




def plan_event(user_input, gemini_parser, calender_manager):
    # 1. First, check if the user wants to *find* a time or *create* an event.
    #    You'll need a simple classifier for this. For now, let's assume if
    #    the prompt contains keywords like "find a time," "schedule for me,"
    #    or "when am I free," we trigger the suggestion workflow.
    
    if True:
        print("Finding available times...")
        
        # 2. Get free/busy data from the CalendarManager.
        #    You'll need to decide the date range to check (e.g., next 7 days).
        #    Let's assume get_free_busy_slots takes a start and end date.
        
        # This is a placeholder; you'll need to implement this logic.
        start_date = '2025-08-20T00:00:00Z'
        end_date = '2025-08-27T00:00:00Z'
        free_busy_data = calender_manager.get_free_busy_slots(start_date, end_date)
        
        # 3. Call the new GeminiParser method.
        suggestions_str = gemini_parser.suggest_time(user_input, free_busy_data)
        
        if suggestions_str:
            # suggestions_data = json.loads(suggestions_json_str)
            print("Here are some suggested times:")
            return suggestions_str
            # for suggestion in suggestions_data.get('suggestions', []):
            #     print(f"- {suggestion}")
        else:
            print("Could not generate suggestions. Please try again.")

def plan_recurring_event(user_input, gemini_parser, calender_manager):
    print("Finding available times...")
    if True:
        # 2. Get free/busy data from the CalendarManager.
        #    You'll need to decide the date range to check (e.g., next 7 days).
        #    Let's assume get_free_busy_slots takes a start and end date.
        
        # This is a placeholder; you'll need to implement this logic.
        
        now_utc = datetime.now(timezone.utc).isoformat()
        now_utc = now_utc[:-6]+'Z'
        week_from_now_utc = (datetime.now(timezone.utc) + dt.timedelta(days=30)).isoformat()
        week_from_now_utc = week_from_now_utc[:-6] +'Z'
        free_busy_data = calender_manager.get_free_busy_slots(now_utc, week_from_now_utc)
        
        # 3. Call the new GeminiParser method.
        suggestions_str = gemini_parser.suggest_recurring_event(user_input, free_busy_data)
        
        if suggestions_str:
            # suggestions_data = json.loads(suggestions_json_str)
            print("Here are some suggested times:")
            return suggestions_str
            # for suggestion in suggestions_data.get('suggestions', []):
            #     print(f"- {suggestion}")
        else:
            print("Could not generate suggestions. Please try again.")

def main():

    #get info from user about morning r day person. Do they want a day off without work. do they want to work at a stretch.  Do they want to break up

    # get user to add specifics like: I want to have 15 mins sessions

    print("Welcome to the AI Calender Scheduler!")

    calender_manager = CalendarManager()
    gemini_parser = GeminiParser()

    user_input = input("Enter your event details: ")

    prompt ="""Studying event Every Monday: 7:00 PM - 9:00 PM (2 hours)
Studying event Every Tuesday: 7:00 PM - 9:00 PM (2 hours)
Studying event Every Wednesday: 7:00 PM - 9:00 PM (2 hours)
Studying event Every Thursday: 7:00 PM - 9:00 PM (2 hours)
Studying event Every Friday: 7:00 PM - 8:00 PM (1 hour)
Studying event Every Saturday: 7:00 AM - 8:00 AM (1 hour)"""


    # print(create_event(prompt, gemini_parser, calender_manager))
    print(gemini_parser.parse_event_details(prompt))
    create_event_1(prompt, gemini_parser,calender_manager)

     
    


if __name__ == "__main__":
    main()
        


