"""Legacy facade with the original list-of-dictionaries response shape."""

from typing import Dict, List, Union

from currency_quote.application.ports.inbound.controller import IController
from currency_quote.client import CurrencyQuoteClient


class ClientBuilder(IController):
    """v5-style dict client. Prices are now decimal strings for both endpoints."""

    def __init__(self, currency_list: Union[List[str], str], **options):
        self.currency_list = currency_list
        self._client = CurrencyQuoteClient(currency_list, **options)
        self.currency_obj = self._client.currency_obj

    def get_last_quote(self) -> List[Dict[str, object]]:
        return self._client.get_last_quote().to_dict()

    def get_history_quote(self, reference_date: int) -> List[Dict[str, object]]:
        return self._client.get_history_quote(reference_date).to_dict()

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()
