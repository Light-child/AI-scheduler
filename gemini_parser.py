#Purpose: This module is responsible for all interactions with the Gemini AI API. 
# Its primary job is to take raw, natural language text input from the user and convert it into structured data
# (like a JSON object) that describes a calendar event.
import os
import json
import re
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import google.generativeai as genai
import datetime


#Key Functionality:
class GeminiParser:
    #Loading the Gemini API key from .env.
    def __init__(self):
        #look for .env file and load its variables
        load_dotenv()
        #retrieve API key
        api_key = os.getenv("GEMINI_API_KEY")
        #if API key not found
        if not api_key:
            raise ValueError("\"GEMINI_API_KEY\" is not found in .env file")
        #present the API key to the google library to validate and allow you to usethe library
        genai.configure(api_key=api_key)
        #Initializing the GEmini model.
        self.model= genai.GenerativeModel('gemini-1.5-flash')
    
    def parse_event_details(self,user_input):
        #This is the pace for your logic for interacting with the AI model
        now = datetime.datetime.now()
        current_date_str = now.strftime("%Y-%m-%d %H:%M:%S")

        prompt = f"""
        The current date and time is {current_date_str}.
        Keeping in mind the RRULE as it depends on the case.
        Extract event details from the following text and return a JSON object.
        if there a multiple events mentioned, make multiple json objects.
        The JSON object MUST have the following keys: "summary" (string), "description" (string), "start_time" (string), and "end_time" (string).
        The time values must be in the exact ISO 8601 format: YYYY-MM-DDTHH:MM:SS-HH:MM (e.g., "2023-10-27T10:00:00-05:00").
        ONly if there is reccurenge:
        "recurrence" (String) (e.g"RRULE:FREQ=WEEKLY;BYDAY=TU;UNTIL=20251231T235959Z")

        Infer the current date if no date is specified. Infer an end time 60 minutes after the start time if not specified.
        If the text is a request to find an available time, return a JSON with a single key "request_type" and value "availability_check".

        User text: "{user_input}"
        """
        try:
            response = self.model.generate_content(prompt)
            #response should bee a json file
            # cleaned_response_text = response.text.strip("` \n")
            # cleaned_response_text = cleaned_response_text.replace("json\n", "", 1)
            return response
        except Exception as e:
            return f"Error interacting wih Gemini. Error: {e}"
        
    def avaiable_models(self):
        print("List of avilable models")
        lst = []
        try:
            for model in genai.list_models():
                # Checking if model supports 'generateContent'
                if 'generateContent' in model.supported_generation_methods:
                    #model.name returns "models/{model_name}"
                    #We woul remove the "models/"
                    model_id = model.name.split('/')[-1]
                    lst.append(model_id)
                    print(f"-{model.name} (Supports generateContent)")
            return lst
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
        
    def suggest_time(self, user_prompt, free_busy_data):
        """
        Generates scheduling suggestions based on user input and calendar availability.
        """
        # Convert the free_busy_data into a string that's easy for the AI to understand.
        busy_slots_str = "I am busy during these times (UTC): "
        if free_busy_data and free_busy_data['busy']:
            for slot in free_busy_data['busy']:
                busy_slots_str += f"from {slot['start']} to {slot['end']}. "
        else:
            busy_slots_str += "I have no known busy times."

        # Craft the new prompt for Gemini.
        prompt = (
            f"The user wants to schedule an event. User request: '{user_prompt}'. "
            f"Here are my current busy times: {busy_slots_str} "
            "Please suggest 3 available times for the user's event."
            "The format of your response should be something like : 'a. Have the cotton event at 8:00am this friday  this \n"
            "'b. Have the cotton event at 5:00pm on Tuesday 26th August, 2025 \n c.Heve cotton event at noon tommorow'" \
            "There should be no other information given except from the suggestions in the format above"
            
        )

        try:
            response = self.model.generate_content(prompt)
            # Assuming the response is a JSON string, you'll need to parse it.
            # Use a library like 'json' or 'json5' for robust parsing.
            return response.text
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return None
    def suggest_recurring_event(self, user_prompt, free_busy_data):
         # Convert the free_busy_data into a string that's easy for the AI to understand.
        busy_slots_str = "I am busy during these times (UTC): "
        if free_busy_data and free_busy_data['busy']:
            for slot in free_busy_data['busy']:
                busy_slots_str += f"from {slot['start']} to {slot['end']}. "
        else:
            busy_slots_str += "I have no known busy times."

        
#         # Craft the new prompt for Gemini.
        prompt = (
            f"The user wants to schedule a recurring  event. User request: '{user_prompt}'. "
            f"Here are my current busy times: {busy_slots_str} "
            "All times in the user's input are in UTC. Please convert all timestamps to Central Daylight Time (CDT), which is UTC-5"
            "Look for times in the users week to place this event"
            "Please suggest  available times for the user's event."
            "Suggested  times must match perfectly with the user's busy times"
            "Try to make the number of hours as close as possible to that which is specified" 
            "To create a feasible schedule, consider breaking the hours into smaller, more manageable chunks across multiple days."
            "chunks can be as shoert as 15 mins and can be as long as 7 hours"
            "The format of your response should be this. The times, dates and comments can be changed but the form of the sentences should be the same: "
            """
**Option 1:  Distributed Schedule**

This option attempts to evenly distribute the 10 hours over multiple days.

Gaming event Every Monday: 8:00 PM - 10:00 PM (2 hours)
Gaming event Every Tuesday: 8:00 PM - 10:00 PM (2 hours)
Gaming event Every Wednesday: 8:00 PM - 10:00 PM (2 hours)
Gaming event Every Thursday: 8:00 PM - 10:00 PM (2 hours)
Gaming event Every Friday: 8:00 PM - 10:00 PM (2 hours)


**Option 2: Weekend Focus**

This concentrates the gaming time on the weekend, sacrificing weekday flexibility.

Gaming event Every Saturday: 10:00 AM - 4:00 PM (6 hours)
Gaming event Every Sunday: 10:00 AM - 2:00 PM (4 hours)"
Do not give any extra information 
"""            
        )
        # prompt = f"""Here are the user's current busy times: {busy_slots_str}.All times in the user's input are in UTC. 
        # Please convert all timestamps to Central Daylight Time (CDT) 
        # , which is UTC-5". 
        # return the users busy times in natural language """
        try:
            response = self.model.generate_content(prompt)
            # Assuming the response is a JSON string, you'll need to parse it.
            # Use a library like 'json' or 'json5' for robust parsing.
            return response.text
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return None

    def parse_event_details_1(user_input: str) -> list[dict]:
        """
        Parses a structured event string and converts it into a list of
        dictionaries suitable for a calendar API.

        This function is optimized for a specific, predictable string format
        and does not use a large language model.

        Args:
            user_input (str): The structured string containing event details,
                            e.g., "Gaming event Every Monday: 8:00 PM - 10:00 PM (2 hours)".

        Returns:
            list[dict]: A list of dictionaries, where each dictionary
                        represents an event with 'summary', 'description',
                        'start_time', 'end_time', and 'recurrence' keys.
                        The time values are in ISO 8601 format.
        """
        # A list to store the dictionaries for each parsed event.
        events = []
        
        # A mapping of day names to their RRULE code (e.g., "MO", "TU").
        day_to_rrule = {
            "Monday": "MO", "Tuesday": "TU", "Wednesday": "WE",
            "Thursday": "TH", "Friday": "FR", "Saturday": "SA",
            "Sunday": "SU"
        }

        # The fixed end date for all recurring rules, as per your prompt.
        rrule_until = "20251231T235959Z"

        # Split the input string into individual lines for each event.
        lines = user_input.strip().split('\n')

        # Regular expression to capture event details from each line.
        # It looks for:
        # 1. The event summary (e.g., "Gaming event").
        # 2. The day of the week (e.g., "Monday").
        # 3. The start time (e.g., "8:00 PM").
        # 4. The end time (e.g., "10:00 PM").
        pattern = re.compile(r"^(.*)Every (\w+):\s*(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M).*$")

        # Iterate through each line of the input.
        for line in lines:
            match = pattern.match(line.strip())
            if not match:
                # Skip lines that don't match the expected pattern.
                continue
            
            # Extract the matched groups.
            summary = match.group(1).strip()
            day_of_week_str = match.group(2)
            start_time_str = match.group(3)
            end_time_str = match.group(4)
            
            # Convert the day of the week string to the RRULE format.
            rrule_day = day_to_rrule.get(day_of_week_str)
            if not rrule_day:
                # If the day name is not recognized, skip this line.
                continue
            
            # Get the current date and time with the system's local timezone.
            now = datetime.now(timezone.utc).astimezone()
            
            # Determine the date of the next occurrence of the specified day of the week.
            # This is important for creating a valid start_time datetime object.
            today_weekday = now.weekday()  # Monday is 0, Sunday is 6
            target_weekday = list(day_to_rrule.keys()).index(day_of_week_str)
            days_until_next = (target_weekday - today_weekday + 7) % 7
            next_occurrence = now.date() + timedelta(days=days_until_next)

            # Parse the start and end times from the strings.
            # The format code for AM/PM is %I:%M %p.
            start_time_obj = datetime.strptime(start_time_str, '%I:%M %p').time()
            end_time_obj = datetime.strptime(end_time_str, '%I:%M %p').time()
            
            # Combine the date and time objects to create full datetime objects
            # with the correct timezone information.
            start_datetime = datetime.combine(next_occurrence, start_time_obj, tzinfo=now.tzinfo)
            end_datetime = datetime.combine(next_occurrence, end_time_obj, tzinfo=now.tzinfo)
            
            # Format the datetime objects into the required ISO 8601 string.
            iso_start_time = start_datetime.isoformat()
            iso_end_time = end_datetime.isoformat()
            
            # Create the recurrence rule string.
            recurrence_rule = f"RRULE:FREQ=WEEKLY;BYDAY={rrule_day};UNTIL={rrule_until}"
            
            # Construct the dictionary for this event.
            event_dict = {
                "summary": summary,
                "description": f"{summary} on {day_of_week_str}",
                "start_time": iso_start_time,
                "end_time": iso_end_time,
                "recurrence": recurrence_rule
            }
            
            # Add the dictionary to our list of events.
            events.append(event_dict)

        return events
 #change

# Example Usage:
# This demonstrates how the function would process your input.

if __name__ == "__main__":
    gem = GeminiParser()
    test_string = """
Gaming event Every Monday: 8:00 PM - 10:00 PM (2 hours)
Gaming event Every Tuesday: 8:00 PM - 10:00 PM (2 hours)
Gaming event Every Wednesday: 8:00 PM - 10:00 PM (2 hours)
Gaming event Every Thursday: 8:00 PM - 10:00 PM (2 hours)
Gaming event Every Friday: 8:00 PM - 10:00 PM (2 hours)
"""
    
    parsed_events =gem.parse_event_details(test_string)
    
    # Print the resulting list of dictionaries, formatted nicely.
    
    # print(json.dumps(parsed_events, indent=2))
    print(parsed_events)





#Defining the prompt that instructs Gemini on what information to extract (summary, description, start time, end time, etc.) and in what format (e.g., JSON).
#Sending the user's text input to the Gemini API.
#Parsing Gemini's response to extract the structured event data.
#Handling potential errors or ambiguities from the AI's response.
#Connection: main.py will call functions within this module to process user input.

