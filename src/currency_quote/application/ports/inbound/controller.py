"""Legacy dictionary-based client contract."""

from abc import ABC, abstractmethod
from typing import Dict, List


class IController(ABC):
    @abstractmethod
    def get_last_quote(self) -> List[Dict[str, object]]:
        """Return the most recent quote for each configured pair."""

    @abstractmethod
    def get_history_quote(self, reference_date: int) -> List[Dict[str, object]]:
        """Return the quote for an earlier day."""
