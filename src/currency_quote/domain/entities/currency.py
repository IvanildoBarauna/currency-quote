"""Core domain entities: validated input pairs and quote results."""

import json
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from typing import Any, Iterator, List, Sequence, Union

from currency_quote.exceptions import (
    InvalidCurrencyFormatError,
    InvalidCurrencyTypeError,
)

CurrencyInput = Union[str, Sequence[str]]

_VALID_CODE_LENGTHS = (3, 4)


def _normalize_pair(pair: Any) -> str:
    if not isinstance(pair, str):
        raise InvalidCurrencyTypeError(
            f"Currency pair must be a string, got {type(pair).__name__}: {pair!r}"
        )

    normalized = pair.strip().upper().replace("/", "-").replace("_", "-")

    parts = normalized.split("-")
    if len(parts) != 2:
        raise InvalidCurrencyFormatError(
            f"Currency pair must be in the format 'USD-BRL', got {pair!r}"
        )

    base_currency, quote_currency = parts
    if (
        len(base_currency) not in _VALID_CODE_LENGTHS
        or len(quote_currency) not in _VALID_CODE_LENGTHS
    ):
        raise InvalidCurrencyFormatError(
            "Each currency code must have 3 characters, e.g. 'USD-BRL'. "
            f"Got {pair!r}"
        )

    if not base_currency.isalpha() or not quote_currency.isalpha():
        raise InvalidCurrencyFormatError(
            f"Currency codes must contain only letters, e.g. 'USD-BRL'. Got {pair!r}"
        )

    return normalized


class CurrencyObject:
    """A validated, normalized collection of currency pairs.

    Accepts a single pair or any sequence of pairs. Input is normalized to
    uppercase with a ``-`` separator, so ``"usd/brl"`` and ``"USD-BRL"`` are
    equivalent. Duplicates are removed while preserving order.
    """

    def __init__(self, currency_list: CurrencyInput):
        if isinstance(currency_list, str):
            candidates = [currency_list]
        elif isinstance(currency_list, Sequence):
            candidates = list(currency_list)
        else:
            raise InvalidCurrencyTypeError(
                "Currency list must be a list or a string, "
                "e.g. ['USD-BRL'] or only 'USD-BRL'"
            )

        if len(candidates) == 0:
            raise InvalidCurrencyFormatError("Currency list is empty")

        normalized: List[str] = []
        for pair in candidates:
            value = _normalize_pair(pair)
            if value not in normalized:
                normalized.append(value)

        self.currency_list = normalized

    def get_currency_list(self) -> List[str]:
        """Return the validated currency pairs."""
        return self.currency_list

    def __iter__(self) -> Iterator[str]:
        return iter(self.currency_list)

    def __len__(self) -> int:
        return len(self.currency_list)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CurrencyObject):
            return self.currency_list == other.currency_list
        return NotImplemented

    def __hash__(self) -> int:
        return hash(tuple(self.currency_list))

    def __repr__(self) -> str:
        return f"CurrencyObject({self.currency_list!r})"


def _now_timestamp() -> int:
    return int(datetime.now().timestamp())


@dataclass
class CurrencyQuote:  # pylint: disable=too-many-instance-attributes
    """A single currency pair quote.

    Supports both attribute access (``quote.bid_price``) and mapping-style
    access (``quote["bid_price"]``) so existing dict-based code keeps working.
    """

    currency_pair: str
    currency_pair_name: str
    base_currency_code: str
    quote_currency_code: str
    quote_timestamp: int
    bid_price: float
    ask_price: float
    quote_extracted_at: int = field(default_factory=_now_timestamp)

    @property
    def quote_datetime(self) -> datetime:
        """The quote timestamp as a timezone-naive local ``datetime``."""
        return datetime.fromtimestamp(self.quote_timestamp)

    @property
    def spread(self) -> float:
        """Difference between ask and bid price."""
        return float(self.ask_price) - float(self.bid_price)

    @property
    def mid_price(self) -> float:
        """Midpoint between bid and ask price."""
        return (float(self.ask_price) + float(self.bid_price)) / 2

    def to_dict(self) -> dict:
        """Return the quote as a plain dictionary."""
        return asdict(self)

    def keys(self) -> List[str]:
        """Field names, enabling ``dict(quote)``."""
        return [f.name for f in fields(self)]

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError as exc:
            raise KeyError(key) from exc

    def get(self, key: str, default: Any = None) -> Any:
        """Mapping-style accessor with a default."""
        return getattr(self, key, default)

    def items(self):
        """Mapping-style ``(key, value)`` pairs."""
        return self.to_dict().items()


class QuoteList(List[CurrencyQuote]):
    """A list of :class:`CurrencyQuote` with convenient export helpers."""

    def to_dict(self) -> List[dict]:
        """Return the quotes as a list of plain dictionaries."""
        return [quote.to_dict() for quote in self]

    def to_json(self, **kwargs: Any) -> str:
        """Serialize the quotes to a JSON string."""
        kwargs.setdefault("ensure_ascii", False)
        return json.dumps(self.to_dict(), **kwargs)

    def to_dataframe(self):
        """Return the quotes as a ``pandas.DataFrame``.

        Requires the optional ``pandas`` extra::

            pip install "currency-quote[pandas]"
        """
        try:
            import pandas as pd  # pylint: disable=import-outside-toplevel
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise ImportError(
                "pandas is required for to_dataframe(). "
                'Install it with: pip install "currency-quote[pandas]"'
            ) from exc

        return pd.DataFrame(self.to_dict())

    def filter_by_pair(self, currency_pair: str) -> "QuoteList":
        """Return only the quotes matching ``currency_pair``."""
        target = _normalize_pair(currency_pair)
        return QuoteList(q for q in self if q.currency_pair == target)

    @property
    def pairs(self) -> List[str]:
        """Distinct currency pairs present in the result, in order."""
        seen: List[str] = []
        for quote in self:
            if quote.currency_pair not in seen:
                seen.append(quote.currency_pair)
        return seen
