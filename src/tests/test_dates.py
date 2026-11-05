import pytest
from datetime import date, datetime, timedelta

from currency_quote.exceptions import InvalidDateError
from currency_quote.utils.dates import normalize_date, to_date, validate_past_date


@pytest.mark.parametrize(
    "value,expected",
    [
        (20240626, 20240626),
        ("20240626", 20240626),
        ("2024-06-26", 20240626),
        ("2024/06/26", 20240626),
        (date(2024, 6, 26), 20240626),
        (datetime(2024, 6, 26, 13, 45), 20240626),
    ],
)
def test_normalize_date_accepts_multiple_formats(value, expected):
    assert normalize_date(value) == expected


def test_normalize_date_accepts_iso_datetime_string():
    assert normalize_date("2024-06-26T13:45:00") == 20240626


@pytest.mark.parametrize(
    "value",
    [220621, 999999999, "", "not-a-date", "2024-13-45", None, 3.5, True],
)
def test_normalize_date_rejects_invalid_values(value):
    with pytest.raises(InvalidDateError):
        normalize_date(value)


def test_to_date_returns_date_object():
    assert to_date("2024-06-26") == date(2024, 6, 26)


def test_validate_past_date_accepts_yesterday():
    yesterday = date.today() - timedelta(days=1)
    assert validate_past_date(yesterday) == int(yesterday.strftime("%Y%m%d"))


def test_validate_past_date_rejects_today():
    with pytest.raises(InvalidDateError, match="strictly before today"):
        validate_past_date(date.today())


def test_validate_past_date_rejects_future():
    with pytest.raises(InvalidDateError):
        validate_past_date(date.today() + timedelta(days=10))
