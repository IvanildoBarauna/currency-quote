# src/currency_quote/domain/entities/currency.py
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from currency_quote.exceptions import (
    CurrencyPairValidationError,
    InvalidCurrencyPairError,
)
from currency_quote.utils.dataframe import build_dataframe, PANDAS_INSTALL_HINT


class CurrencyObject:
    """Validated, normalized container for one or more currency pairs."""

    MAXIMUM_CODE_LENGTH = 4

    def __init__(self, currency_list: Union[list, str]):
        if not isinstance(currency_list, (list, str)):
            raise InvalidCurrencyPairError(
                "Currency list must be a list or a string, e.g. ['USD-BRL'] or only 'USD-BRL'"
            )

        if isinstance(currency_list, str):
            currency_list = [currency_list]

        if len(currency_list) == 0:
            raise CurrencyPairValidationError("Currency list is empty")

        normalized_list = []
        for currency in currency_list:
            try:
                base_currency, quote_currency = currency.strip().split("-")
            except ValueError as exc:
                raise CurrencyPairValidationError(
                    "Currency pair must be in the format 'USD-BRL'"
                ) from exc

            if not len(base_currency) in (3, self.MAXIMUM_CODE_LENGTH) or not len(
                quote_currency
            ) in (3, self.MAXIMUM_CODE_LENGTH):
                raise CurrencyPairValidationError(
                    "Each currency code must have 3 characters, e.g. 'USD-BRL'"
                )

            normalized_list.append("-".join((base_currency, quote_currency)).upper())

        self.currency_list = normalized_list

    def get_currency_list(self) -> List[str]:
        return self.currency_list


@dataclass
class CurrencyQuote:  # pylint: disable=too-many-instance-attributes
    """Typed quote result with optional daily statistics when available."""

    currency_pair: str
    currency_pair_name: str
    base_currency_code: str
    quote_currency_code: str
    quote_timestamp: int
    bid_price: float
    ask_price: float
    quote_extracted_at: int = field(
        default_factory=lambda: int(datetime.now().timestamp())
    )
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    var_bid: Optional[float] = None
    pct_change: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the quote to a plain dict with a stable schema."""
        return {
            "currency_pair": self.currency_pair,
            "currency_pair_name": self.currency_pair_name,
            "base_currency_code": self.base_currency_code,
            "quote_currency_code": self.quote_currency_code,
            "quote_timestamp": self.quote_timestamp,
            "bid_price": self.bid_price,
            "ask_price": self.ask_price,
            "quote_extracted_at": self.quote_extracted_at,
            "high_price": self.high_price,
            "low_price": self.low_price,
            "var_bid": self.var_bid,
            "pct_change": self.pct_change,
        }

    def to_dataframe(self):
        """Export this single quote as a one-row ``pandas.DataFrame``."""
        try:
            return build_dataframe([self.to_dict()])
        except ImportError as exc:
            raise ImportError(PANDAS_INSTALL_HINT) from exc

    def trading_date(self) -> date:
        """UTC calendar date of the quote (matches the API's daily granularity)."""
        return datetime.utcfromtimestamp(self.quote_timestamp).date()


class QuoteList(List[CurrencyQuote]):
    """List of :class:`CurrencyQuote` with convenient exports."""

    def to_dataframe(self):
        """Export the whole result set as a ``pandas.DataFrame``."""
        try:
            return build_dataframe([quote.to_dict() for quote in self])
        except ImportError as exc:
            raise ImportError(PANDAS_INSTALL_HINT) from exc
