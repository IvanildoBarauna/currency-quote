"""Validation for dates supported by the historical quote endpoint."""

from datetime import date, datetime


def validate_reference_date(reference_date: int) -> None:
    """Require a real YYYYMMDD date strictly before today."""
    if isinstance(reference_date, bool) or not isinstance(reference_date, int):
        raise ValueError("reference_date must be an integer in YYYYMMDD format")
    try:
        parsed_date = datetime.strptime(str(reference_date), "%Y%m%d").date()
    except ValueError as exc:
        raise ValueError(
            "reference_date must be a valid date in YYYYMMDD format"
        ) from exc
    if parsed_date.strftime("%Y%m%d") != str(reference_date):
        raise ValueError("reference_date must be a valid date in YYYYMMDD format")
    if parsed_date >= date.today():
        raise ValueError("reference_date must be before today")
