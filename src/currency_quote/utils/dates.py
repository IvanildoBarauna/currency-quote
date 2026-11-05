# src/currency_quote/utils/dates.py
"""Flexible date parsing for history requests.

Accepted input formats for a reference date:
  - compact int: 20220101
  - ISO string: "2022-01-01"
  - compact string: "20220101"
  - brazilian date: "01/01/2022"
  - ``datetime.date`` / ``datetime.datetime`` instances
"""
from datetime import date, datetime
from typing import Union

from currency_quote.exceptions import InvalidDateError

_MIN_YEAR = 1900
_COMPACT_FORMAT = "%Y%m%d"

_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y")


def parse_reference_date(value: Union[int, str, date, datetime]) -> int:
    """Normalize any supported date input to a compact int (e.g. 20220101).

    Raises:
        InvalidDateError: if the value is malformed, in the future or too old.
    """
    if isinstance(value, bool):
        raise InvalidDateError("Reference date must be an int, str, date or datetime.")

    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    elif isinstance(value, int):
        parsed = _parse_compact(value)
    elif isinstance(value, str):
        parsed = _parse_string(value)
    else:
        raise InvalidDateError(
            f"Unsupported date type {type(value).__name__!r}; use an int, str, date or datetime."
        )

    _validate(parsed, original=value)
    return int(parsed.strftime(_COMPACT_FORMAT))


def compact_to_date(value: int) -> date:
    """Convert a compact date int (e.g. 20220101) into a ``date`` without range checks."""
    return _parse_compact(value)


def _parse_compact(value: int) -> date:
    text = str(value)
    if len(text) != 8:
        raise InvalidDateError(
            f"Invalid reference date {value!r}; expected a calendar date like 20220101."
        )
    try:
        return datetime.strptime(text, _COMPACT_FORMAT).date()
    except ValueError as exc:
        raise InvalidDateError(
            f"Invalid reference date {value!r}; expected a calendar date like 20220101."
        ) from exc


def _parse_string(value: str) -> date:
    text = value.strip()
    if text.isdigit():
        return _parse_compact(int(text))  # type: ignore[arg-type]
    for date_format in _DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    raise InvalidDateError(
        f"Invalid reference date {value!r}; expected 'YYYY-MM-DD', 'YYYYMMDD' or 'DD/MM/YYYY'."
    )


def _validate(parsed: date, original: Union[int, str, date, datetime]) -> None:
    if parsed.year < _MIN_YEAR:
        raise InvalidDateError(
            f"Reference date {original!r} is too old (min year {_MIN_YEAR})."
        )
    if parsed > date.today():
        raise InvalidDateError(
            f"Reference date {original!r} must not be in the future."
        )


def assert_valid_range(start_date: int, end_date: int) -> None:
    """Validate a compact-date range (start <= end)."""
    if start_date > end_date:
        raise InvalidDateError(
            f"start_date {start_date} must be earlier than or equal to end_date {end_date}."
        )
