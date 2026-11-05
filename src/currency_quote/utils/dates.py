"""Date parsing and provider-local trading calendar rules."""

from datetime import date, datetime
from typing import Union
from zoneinfo import ZoneInfo

from currency_quote.exceptions import InvalidDateError

DateInput = Union[int, str, date, datetime]
PROVIDER_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def parse_date(value: DateInput) -> date:
    """Parse YYYYMMDD, YYYY-MM-DD, DD/MM/YYYY or a date/datetime."""
    if isinstance(value, datetime):
        result = (
            value.astimezone(PROVIDER_TIMEZONE).date() if value.tzinfo else value.date()
        )
    elif isinstance(value, date):
        result = value
    elif isinstance(value, bool):
        raise InvalidDateError("Date must not be a boolean")
    elif isinstance(value, (int, str)):
        text = str(value).strip()
        result = None
        for pattern in ("%Y%m%d", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                parsed = datetime.strptime(text, pattern).date()
                if parsed.strftime(pattern) == text:
                    result = parsed
                    break
            except ValueError:
                continue
        if result is None:
            raise InvalidDateError(
                f"Invalid date {value!r}; use YYYYMMDD or YYYY-MM-DD"
            )
    else:
        raise InvalidDateError(f"Unsupported date type: {type(value).__name__}")
    if result >= datetime.now(PROVIDER_TIMEZONE).date():
        raise InvalidDateError(
            "Historical date must be before today in America/Sao_Paulo"
        )
    return result


def trading_date(payload: dict, timestamp: int) -> date:
    """Prefer the provider's local create_date; fall back to its Unix timestamp."""
    created = payload.get("create_date")
    if isinstance(created, str):
        try:
            return datetime.strptime(created[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    return datetime.fromtimestamp(timestamp, PROVIDER_TIMEZONE).date()
