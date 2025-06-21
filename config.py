import os
from dotenv import load_dotenv

load_dotenv()  # load .env by default

class Config:
    GOOGLE_TOKEN_PATH = os.getenv('GOOGLE_TOKEN_PATH', 'token.pickle')
    CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON', 'credentials.json')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    TIMEZONE = os.getenv('TIMEZONE', 'US/Pacific')

    # Map nicknames to full contact names
    KNOWN_CONTACTS = {
        "john": "Johnathan Smith",
        "sarah": "Sarah Kapoor",
        "raj": "Raj Mehta",
        "viv": "Vivek Singh",
        "amy": "Amelia Zhang"
    }
