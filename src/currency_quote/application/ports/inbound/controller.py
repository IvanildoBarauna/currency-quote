# src/currency_quote/application/ports/inbound/controller.py
from abc import ABC, abstractmethod
from typing import List


class IController(ABC):
    """Port implemented by library entry points (e.g. ClientBuilder)."""

    @abstractmethod
    def __init__(self, currency_list: list):
        pass

    @abstractmethod
    def get_last_quote(self) -> List[dict]:
        pass

    @abstractmethod
    def get_history_quote(self, reference_date: int) -> List[dict]:
        pass
