"""Currency pair inputs and provider-independent quote values."""

from dataclasses import dataclass, field
from decimal import Decimal
from time import time
from typing import Dict, List, Union

from currency_quote.exceptions import InvalidCurrencyError, InvalidCurrencyTypeError


class CurrencyObject:
    """Normalize pairs once, preserving their order and removing duplicates."""

    def __init__(self, currency_list: Union[List[str], str]):
        if isinstance(currency_list, str):
            currency_list = [currency_list]
        if not isinstance(currency_list, list):
            raise InvalidCurrencyTypeError("Currency list must be a list or a string")
        if not currency_list:
            raise InvalidCurrencyError("Currency list is empty")

        pairs = []
        for pair in currency_list:
            if not isinstance(pair, str):
                raise InvalidCurrencyTypeError("Each currency pair must be a string")
            parts = pair.strip().upper().split("-")
            if len(parts) != 2:
                raise InvalidCurrencyError(
                    "Currency pair must be in the format 'USD-BRL'"
                )
            if any(
                len(code) not in (3, 4) or not code.isascii() or not code.isalpha()
                for code in parts
            ):
                raise InvalidCurrencyError(
                    "Each currency code must have 3 or 4 ASCII letters, e.g. 'USD-BRL'"
                )
            normalized = "-".join(parts)
            if normalized not in pairs:
                pairs.append(normalized)
        self.currency_list = pairs

    def get_currency_list(self) -> List[str]:
        return list(self.currency_list)


@dataclass
class CurrencyQuote:  # pylint: disable=too-many-instance-attributes
    """A quote with exact decimal prices and an extraction time per instance."""

    currency_pair: str
    currency_pair_name: str
    base_currency_code: str
    quote_currency_code: str
    quote_timestamp: int
    bid_price: Decimal
    ask_price: Decimal
    quote_extracted_at: int = field(default_factory=lambda: int(time()))
    high_price: Union[Decimal, None] = None
    low_price: Union[Decimal, None] = None
    var_bid: Union[Decimal, None] = None
    pct_change: Union[Decimal, None] = None

    def to_dict(self) -> Dict[str, object]:
        """Return the stable legacy schema with JSON-ready decimal strings."""
        return {
            "currency_pair": self.currency_pair,
            "currency_pair_name": self.currency_pair_name,
            "base_currency_code": self.base_currency_code,
            "quote_currency_code": self.quote_currency_code,
            "quote_timestamp": self.quote_timestamp,
            "bid_price": str(self.bid_price),
            "ask_price": str(self.ask_price),
            "quote_extracted_at": self.quote_extracted_at,
        }
