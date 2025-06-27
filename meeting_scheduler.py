import datetime
import re
import pytz
import os
import json
import pickle
from dateutil import parser as date_parser
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Google Calendar API imports
GOOGLE_AVAILABLE = True
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ModuleNotFoundError as e:
    print("\n⚠️ Google API libraries not available:", e)
    GOOGLE_AVAILABLE = False

# OpenAI API v1 setup
try:
    from openai import OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception as e:
    print("⚠️ OpenAI client not available:", e)
    client = None

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# Beautified logging helper
def pretty_print(title: str, content: str):
    border = '═' * (len(title) + 4)
    print(f"╔{border}╗")
    print(f"║  {title}  ║")
    print(f"╠{border}╣")
    for line in content.split('\n'):
        print(f"║ {line}")
    print(f"╚{border}╝")

# Nickname contact mapping
KNOWN_CONTACTS = {
    "john": "Johnathan Smith",
    "sarah": "Sarah Kapoor",
    "raj": "Raj Mehta",
    "viv": "Vivek Singh",
    "amy": "Amelia Zhang"
}

# Example prompts for the user
EXAMPLE_PROMPTS = [
    "Set a sync call with Sarah tomorrow at 5pm",
    "Set a 1:1 with Viv next Tuesday at 9:30am",
    "Set a demo with Amy at 2pm",
    "Set a meeting with Raj on Monday at 3pm"
]

class MeetingSchedulerAgent:
    def __init__(self, timezone="US/Pacific"):
        self.timezone = pytz.timezone(timezone)
        self.creds = self.authenticate_google() if GOOGLE_AVAILABLE else None

    def authenticate_google(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token_file:
                creds = pickle.load(token_file)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token_file:
                pickle.dump(creds, token_file)
        return creds

    def resolve_contact_name(self, raw_name):
        key = raw_name.strip().lower()
        return KNOWN_CONTACTS.get(key, raw_name.strip().title())

    def gpt_parse_input(self, user_input):
        today = datetime.datetime.now(self.timezone).strftime("%Y-%m-%d")
        prompt = (
            f"Assume today's date is {today}. "
            "Extract the meeting details from this input. "
            "Return ONLY the JSON object with keys: title, person (name only), "
            "datetime (ISO 8601), duration. Duration should be minutes if provided."\
            f"\nInput: '{user_input}'"
        )
        pretty_print("PROMPT TO GPT", prompt)
        if not client:
            print("⚠️ GPT client is not available: Missing OpenAI API key")
            return None, None, None
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a scheduling assistant. Respond with pure JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            content = response.choices[0].message.content
            pretty_print("RAW GPT RESPONSE", content)
            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?", "", cleaned)
            if cleaned.endswith("```"):
                cleaned = re.sub(r"```$", "", cleaned)
            parsed = json.loads(cleaned.strip())
            dt = date_parser.parse(parsed['datetime'])
            if dt.tzinfo is None:
                dt = self.timezone.localize(dt)
            else:
                dt = dt.astimezone(self.timezone)
            title = parsed['title'].strip()
            person = self.resolve_contact_name(parsed.get('person', 'Unnamed'))
            duration = int(parsed.get('duration', 30))
            return f"{title} with {person}", dt, duration
        except Exception as e:
            print("⚠️ GPT parse failed:", e)
            return None, None, None

    def regex_parse_input(self, user_input):
        match = re.search(
            r"(?i)set a ([\w:/\+\- ]+) (?:meeting|call|appointment)"
            r"(?: with ([^@\d\n]+))?"
            r"(?: on | at )?(.*?)"
            r"(?: for (\d+)\s*(?:minutes?|mins?|hours?|hrs?|hr))?"
            r"$",
            user_input,
        )
        if not match:
            return None, None, None
        title_prefix = match.group(1).strip().capitalize()
        raw_person = match.group(2)
        person = self.resolve_contact_name(raw_person) if raw_person else "Unnamed"
        time_text = match.group(3)
        duration_raw = match.group(4)
        try:
            dt = date_parser.parse(time_text, fuzzy=True)
            if dt.tzinfo is None:
                dt = self.timezone.localize(dt)
            else:
                dt = dt.astimezone(self.timezone)
        except Exception as e:
            print(f"Failed to parse date/time: {e}")
            return None, None, None
        duration = int(duration_raw) if duration_raw else 30
        return f"{title_prefix} with {person}", dt, duration

    def parse_input(self, user_input):
        title, dt, dur = self.gpt_parse_input(user_input)
        if not title:
            print("Falling back to regex parsing...")
            return self.regex_parse_input(user_input)
        return title, dt, dur

    def create_google_event(self, title, start_time, duration_minutes):
        service = build("calendar", "v3", credentials=self.creds)
        end_time = start_time + datetime.timedelta(minutes=duration_minutes)
        event = {
            'summary': title,
            'start': {'dateTime': start_time.isoformat(), 'timeZone': str(start_time.tzinfo)},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': str(start_time.tzinfo)}
        }
        created = service.events().insert(calendarId='primary', body=event).execute()
        return created.get('htmlLink')

    def receive_input(self, user_input):
        title, start_time, duration = self.parse_input(user_input)
        if not title:
            return "Sorry, I couldn't understand that. Try something like 'Set a sync call with Raj at 2pm tomorrow'."
        if GOOGLE_AVAILABLE and self.creds:
            try:
                google_link = self.create_google_event(title, start_time, duration)
                return f"✅ Meeting '{title}' scheduled.\n\n📅 Google Calendar link: {google_link}" 
            except Exception as e:
                return f"❌ Failed to schedule with Google Calendar: {str(e)}"
        return f"📝 Simulated scheduling: '{title}' at {start_time.strftime('%Y-%m-%d %I:%M %p %Z')}"

    def run_interactive(self):
        print("Welcome to MeetingSchedulerAI (GPT-4o)!")
        print("Example prompts:")
        for p in EXAMPLE_PROMPTS:
            print(f" - {p}")
        print("Type 'exit' to quit.\n")
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            response = self.receive_input(user_input)
            print(response)

if __name__ == "__main__":
    agent = MeetingSchedulerAgent()
    agent.run_interactive()
