# src/currency_quote/adapters/inbound/lib_controller.py
"""Backward-compatible facade (v5 style) returning plain dicts."""
from typing import List, Union
from currency_quote.application.ports.inbound.controller import IController
from currency_quote.application.use_cases.get_last_currency_quote import (
    GetLastCurrencyQuoteUseCase,
)
from currency_quote.application.use_cases.get_history_currency_quote import (
    GetHistCurrencyQuoteUseCase,
)
from currency_quote.domain.entities.currency import CurrencyObject
from currency_quote.utils.dates import parse_reference_date


class ClientBuilder(IController):
    """v5-compatible client returning ``List[dict]`` results.

    For typed results, flexible dates and range history, prefer
    :class:`currency_quote.CurrencyQuoteClient`.
    """

    def __init__(self, currency_list: Union[list, str]):
        self.currency_list = currency_list
        self.currency_obj = CurrencyObject(self.currency_list)

    def get_last_quote(self) -> List[dict]:
        quotes = GetLastCurrencyQuoteUseCase.execute(currency_obj=self.currency_obj)
        return [quote.to_dict() for quote in quotes]

    def get_history_quote(self, reference_date: int) -> List[dict]:
        parsed_date = parse_reference_date(reference_date)
        quotes = GetHistCurrencyQuoteUseCase.execute(
            currency_obj=self.currency_obj,
            reference_date=parsed_date,
        )
        return [quote.to_dict() for quote in quotes]
