from typing import Union
from dataclasses import dataclass, field
from datetime import datetime


class CurrencyObject:
    def __init__(self, currency_list: Union[list, str]):
        if not isinstance(currency_list, list) and not isinstance(currency_list, str):
            raise TypeError(
                "Currency list must be a list or a string, e.g. ['USD-BRL'] or only 'USD-BRL'"
            )

        if isinstance(currency_list, str):
            currency_list = [currency_list]

        if len(currency_list) == 0:
            raise ValueError("Currency list is empty")

        for currency in currency_list:
            if not isinstance(currency, str):
                raise TypeError("Each currency pair must be a string")
            try:
                base_currency, quote_currency = currency.split("-")
            except ValueError as exc:
                raise ValueError(
                    "Currency pair must be in the format 'USD-BRL'"
                ) from exc

            if not len(base_currency) in (3, 4) or not len(quote_currency) in (3, 4):
                raise ValueError(
                    "Each currency code must have 3 or 4 characters, e.g. 'USD-BRL'"
                )

            if not base_currency.isalpha() or not quote_currency.isalpha():
                raise ValueError("Currency codes must contain only letters")

        self.currency_list = currency_list

    def get_currency_list(self) -> list:
        return self.currency_list


@dataclass
class CurrencyQuote:  # pylint: disable=too-many-instance-attributes
    currency_pair: str
    currency_pair_name: str
    base_currency_code: str
    quote_currency_code: str
    quote_timestamp: int
    bid_price: str
    ask_price: str
    quote_extracted_at: int = field(default_factory=lambda: int(datetime.now().timestamp()))
