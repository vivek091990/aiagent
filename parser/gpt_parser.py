import json
import re
from datetime import datetime
import pytz
from openai import OpenAI
from dateutil import parser as date_parser
from config import Config
from parser.base_parser import BaseParser

class GPTParser(BaseParser):
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None

    def parse(self, text: str):
        if not self.client:
            raise RuntimeError("OpenAI client not configured")
        today = datetime.now(pytz.timezone(Config.TIMEZONE)).strftime('%Y-%m-%d')
        prompt = (
            f"Assume today's date is {today}. Extract meeting details from: '{text}'. "
            "Output only JSON with keys: title, person, datetime, duration. "
            "Duration should be in minutes if provided; default to 30."
        )
        response = self.client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': 'You are a scheduling assistant. Respond with pure JSON only.'},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.2
        )
        raw = response.choices[0].message.content
        clean = re.sub(r'^```(?:json)?|```$', '', raw.strip())
        data = json.loads(clean)
        dt = date_parser.parse(data['datetime'])
        duration = int(data.get('duration', 30))
        return data['title'], data.get('person', 'Unnamed'), dt, duration
