from abc import ABC, abstractmethod
from datetime import datetime

class BaseParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> (str, str, datetime, int):
        """Return (title, person, datetime, duration_minutes)."""
        pass
