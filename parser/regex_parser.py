import re
from dateutil import parser as date_parser
from config import Config
from parser.base_parser import BaseParser

class RegexParser(BaseParser):
    PATTERN = re.compile(r"(?i)set a ([\w:/\+\- ]+) (?:meeting|call|appointment)(?: with ([^@\d\n]+))?(?: on | at )?(.*?)$")

    def parse(self, text: str):
        m = self.PATTERN.search(text)
        if not m:
            return None, None, None, None
        title_prefix = m.group(1).strip().capitalize()
        person_raw = m.group(2)
        person = Config.KNOWN_CONTACTS.get(person_raw.lower(), person_raw.title()) if person_raw else 'Unnamed'
        time_text = m.group(3)
        dt = date_parser.parse(time_text, fuzzy=True)
        return title_prefix, person, dt, 30