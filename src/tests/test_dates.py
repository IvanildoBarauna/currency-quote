# src/tests/test_dates.py
from datetime import date, datetime

import pytest

from currency_quote.exceptions import InvalidDateError
from currency_quote.utils.dates import assert_valid_range, parse_reference_date


def test_compact_int():
    assert parse_reference_date(20220101) == 20220101


def test_iso_string():
    assert parse_reference_date("2022-01-01") == 20220101


def test_compact_string():
    assert parse_reference_date("20220101") == 20220101


def test_brazilian_string():
    assert parse_reference_date("01/01/2022") == 20220101


def test_date_instance():
    assert parse_reference_date(date(2022, 1, 1)) == 20220101


def test_datetime_instance():
    assert parse_reference_date(datetime(2022, 1, 1, 20, 30)) == 20220101


def test_invalid_string_raises():
    with pytest.raises(InvalidDateError, match="Invalid reference date"):
        parse_reference_date("not-a-date")


def test_invalid_month_raises():
    with pytest.raises(InvalidDateError):
        parse_reference_date("2022-13-01")


def test_incomplete_int_raises():
    with pytest.raises(InvalidDateError, match="expected a calendar date"):
        parse_reference_date(202201)


def test_future_date_raises():
    with pytest.raises(InvalidDateError, match="must not be in the future"):
        parse_reference_date(20991231)


def test_future_datetime_raises():
    with pytest.raises(InvalidDateError):
        parse_reference_date(datetime(2099, 1, 1))


def test_too_old_date_raises():
    with pytest.raises(InvalidDateError, match="too old"):
        parse_reference_date(18991231)


def test_unsupported_type_raises():
    with pytest.raises(InvalidDateError, match="Unsupported date type"):
        parse_reference_date(1.5)


def test_bool_raises():
    with pytest.raises(InvalidDateError):
        parse_reference_date(True)


def test_inverted_range_raises():
    with pytest.raises(InvalidDateError, match="earlier than or equal to"):
        assert_valid_range(20220110, 20220101)


def test_valid_range_passes():
    assert assert_valid_range(20220101, 20220110) is None
