"""Helpers for accepting and normalizing reference dates."""

from datetime import date, datetime
from typing import Union

from currency_quote.exceptions import InvalidDateError

DateInput = Union[int, str, date, datetime]

_DATE_FORMAT = "%Y%m%d"


def normalize_date(value: DateInput) -> int:
    """Normalize a reference date into the ``YYYYMMDD`` integer the API expects.

    Accepts ``datetime``/``date`` objects, ``int`` such as ``20240626``, and
    strings in ``YYYYMMDD``, ``YYYY-MM-DD`` or ISO-8601 form.

    Raises:
        InvalidDateError: If the value cannot be interpreted as a date.
    """
    return int(to_date(value).strftime(_DATE_FORMAT))


def to_date(value: DateInput) -> date:
    """Convert any supported date input into a ``datetime.date``."""
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, bool):
        raise InvalidDateError(f"Invalid reference date: {value!r}")

    if isinstance(value, int):
        text = str(value)
        if len(text) != 8:
            raise InvalidDateError(
                f"Integer dates must be in YYYYMMDD format, got {value!r}"
            )
        return _parse(text, original=value)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise InvalidDateError("Reference date cannot be empty")
        compact = text.replace("-", "").replace("/", "")
        if len(compact) == 8 and compact.isdigit():
            return _parse(compact, original=value)
        try:
            return datetime.fromisoformat(text).date()
        except ValueError as exc:
            raise InvalidDateError(
                f"Could not parse reference date {value!r}. "
                "Use YYYYMMDD, YYYY-MM-DD, or a date/datetime object."
            ) from exc

    raise InvalidDateError(
        f"Unsupported reference date type: {type(value).__name__} ({value!r})"
    )


def _parse(text: str, original: DateInput) -> date:
    try:
        return datetime.strptime(text, _DATE_FORMAT).date()
    except ValueError as exc:
        raise InvalidDateError(
            f"Could not parse reference date {original!r} as YYYYMMDD."
        ) from exc


def validate_past_date(value: DateInput) -> int:
    """Normalize a date and ensure it refers to a day already closed.

    The upstream data source only publishes daily closing quotes for days in
    the past, so today and future dates are rejected.

    Raises:
        InvalidDateError: If the date is today or in the future.
    """
    normalized = normalize_date(value)
    today = int(datetime.today().strftime(_DATE_FORMAT))

    if normalized >= today:
        raise InvalidDateError(
            f"Reference date {normalized} must be strictly before today ({today}). "
            "Historical quotes are only available for closed days; "
            "use get_last_quote() for the current value."
        )

    return normalized
