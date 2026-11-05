"""Port implemented by a supported-pairs provider."""

from abc import ABC, abstractmethod
from typing import Set


class ICurrencyValidator(ABC):
    @abstractmethod
    def available_pairs(self) -> Set[str]:
        """Get the available currency pairs, using a cache where appropriate."""
