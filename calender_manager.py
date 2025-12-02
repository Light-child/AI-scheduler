#All of Google CAlendar API Logic
# calendar_manager.py
import datetime as dt
import os
from datetime import timezone
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.z
# IMPORTANT: Make sure these scopes match what you configured in the Google Cloud Console
SCOPES = ["https://www.googleapis.com/auth/calendar"] # Added freebusy scope
class CalendarManager:
    def __init__(self):
        self.service= self.get_calendar_service()
    def get_calendar_service(self):
        creds = None
        # Check if token.json already exists
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
        # If no valid credentials or expired, initiate the OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request()) # Refresh token if expired
            else:
                # This is the part that triggers the browser for initial authorization
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0) # This opens the browser
            # Save the new/refreshed credentials to token.json
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return build("calendar", "v3", credentials=creds)

    # ... rest of your calendar_manager.py functions
    # You might also want functions to list events for testing purposes

    # def list_events(self, max_results=10):
    #     service = self.get_calendar_service()
    #     now = datetime.datetime.now(datetime.timezone.utc).isoformat() + 'Z' # 'Z' indicates UTC time
    #     events_result = service.events().list(
    #         calendarId='primary', timeMin=now, maxResults=max_results, singleEvents=True,
    #         orderBy='startTime').execute()
    #     events = events_result.get('items', [])
    #     if not events:
    #         print('No upcoming events found.')
    #         return []
    #     print('Upcoming events:')
    #     for event in events:
    #         start = event['start'].get('dateTime', event['start'].get('date'))
    #         print(f"{start} - {event['summary']}")
    #     return events
    
    #Under development
    def add_event(self,event_body):
        """
        Adds an event to the specified Google Calendar.
        Returns:
            dict: The created event resource if successful, None otherwise.
        """
        
        try:
            created_event = self.service.events().insert(body= event_body, calendarId='primary').execute()
            print(f"Event created: {created_event.get('htmlLink')}")
            return created_event

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None
        
    def get_free_busy_slots(self, time_min: str, time_max: str) -> dict:
        """
        Queries the user's calendar for busy times within a given range.

        Args:
            time_min: The start time of the query range (ISO 8601 string).
            time_max: The end time of the query range (ISO 8601 string).

        Returns:
            A dictionary of free/busy data.
        """
        try:
            # Prepare the request body for the free/busy query
            body = {
                "timeMin": time_min,
                "timeMax": time_max,
                "items": [
                    {"id": "primary"}  # Query the user's primary calendar
                ]
            }
            
            # Make the API call
            response = self.service.freebusy().query(body=body).execute()
            
            # The 'calendars' key contains the free/busy data for each queried calendar
            return response.get('calendars', {}).get('primary', {})
        
        except Exception as e:
            print(f"An error occurred while querying free/busy data: {e}")
            return {}
        
    def get_available_slots(self, time_min: str, time_max: str) -> list:
        """
        Orchestrates the process of getting busy data and calculating free slots.
        """
        # Step 1: Call the API to get busy data.
        busy_data = self.get_free_busy_slots(time_min, time_max)
        
        # Extract the list of busy time slots from the dictionary.
        busy_slots = busy_data.get('busy', [])
        
        # Step 2: Pass the list of busy slots to the calculation method.
        free_slots = self.calculate_free_slots(time_min, time_max, busy_slots)
        
        return free_slots



# Example usage (for testing)
if __name__ == "__main__":
    manager = CalendarManager()
    now_utc = datetime.now(timezone.utc).isoformat()
    now_utc = now_utc[:-6]+'Z'
    week_from_now_utc = (datetime.now(timezone.utc) + dt.timedelta(days=30)).isoformat()
    week_from_now_utc = week_from_now_utc[:-6] +'Z'

    # print(f"{now_utc} to {week_from_now_utc}")
    print("New\n New\n New")
    print(manager.get_free_busy_slots(now_utc,week_from_now_utc))