import os
from parser.gpt_parser import GPTParser
from parser.regex_parser import RegexParser
from calendar_client import CalendarClient
from config import Config

class SchedulerAgent:
    def __init__(self):
        # Initialize parsers: GPT first, then regex fallback
        self.parsers = [GPTParser(), RegexParser()]
        # Initialize calendar client if Google token is available
        if Config.GOOGLE_TOKEN_PATH and os.path.exists(Config.GOOGLE_TOKEN_PATH):
            try:
                self.calendar = CalendarClient()
            except Exception:
                # Calendar client could not be created
                self.calendar = None
        else:
            self.calendar = None

    def schedule(self, input_text: str):
        """
        Parse the input_text to extract meeting details, then create the event.
        Returns a confirmation string or an error message.
        """
        for parser in self.parsers:
            try:
                title, person, dt, dur = parser.parse(input_text)
                if title:
                    # Compose the event title using the parsed title and person
                    event_title = f"{title} with {person}"

                    # Create event or simulate
                    if self.calendar:
                        link = self.calendar.create_event(event_title, dt, dur)
                        return f"✅ Scheduled: {event_title}\n👉 {link}"
                    else:
                        return f"📝 Simulated: '{event_title}' at {dt.strftime('%Y-%m-%d %I:%M %p %Z')}"
            except Exception:
                # Try next parser
                continue
        return "❌ Unable to parse meeting request. Please try a different phrasing."
