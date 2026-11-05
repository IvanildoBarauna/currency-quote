"""Fixed AwesomeAPI payloads: malformed data, empty windows and date filtering."""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from currency_quote.adapters.outbound.currency_api import CurrencyAPI
from currency_quote.adapters.outbound.currency_validator_api import CurrencyValidatorAPI
from currency_quote.exceptions import CurrencyAPIError, NoDataForDateError
from currency_quote.utils.dates import PROVIDER_TIMEZONE


def entry(day="2024-06-03", bid="5.10"):
    timestamp = int(
        datetime.fromisoformat(day + "T12:00:00")
        .replace(tzinfo=PROVIDER_TIMEZONE)
        .timestamp()
    )
    return {
        "timestamp": str(timestamp),
        "create_date": day + " 12:00:00",
        "bid": bid,
        "ask": "5.11",
    }


def test_last_quote_missing_pair_does_not_silently_skip():
    http = Mock()
    http.get.return_value = {"USDBRL": entry()}
    with pytest.raises(NoDataForDateError, match="EUR-BRL"):
        CurrencyAPI(http).get_last_quote(["USD-BRL", "EUR-BRL"])


def test_last_quote_valid_and_optional_fields():
    http = Mock()
    http.get.return_value = {
        "USDBRL": {**entry(), "name": "Dólar/Real", "high": "5.25"}
    }
    result = CurrencyAPI(http).get_last_quote(["USD-BRL"])
    assert result[0].bid_price == Decimal("5.10")
    assert result[0].high_price == Decimal("5.25")
    assert result[0].to_dict()["bid_price"] == "5.10"


@pytest.mark.parametrize(
    "response",
    [[], None, {"USDBRL": {"bid": "1"}}, {"USDBRL": {**entry(), "bid": "nan"}}],
)
def test_malformed_last_payload_has_typed_error(response):
    http = Mock()
    http.get.return_value = response
    with pytest.raises(CurrencyAPIError):
        CurrencyAPI(http).get_last_quote(["USD-BRL"])


def test_history_windows_skip_empty_deduplicate_and_filter():
    http = Mock()
    http.get.side_effect = [
        [entry("2024-01-01"), entry("2023-12-31"), entry("2024-01-01")],
        [],
        [entry("2026-01-01")],
    ]
    result = CurrencyAPI(http).get_history(
        "USD-BRL", date(2024, 1, 1), date(2026, 1, 1)
    )
    assert len(result) == 2
    assert len(http.get.call_args_list) == 3
    assert "start_date=20240101" in http.get.call_args_list[0].args[0]
    assert "end_date=20260101" in http.get.call_args_list[-1].args[0]


def test_single_day_empty_response_is_handled_by_use_case():
    from currency_quote import CurrencyQuoteClient

    http = Mock()
    http.get.return_value = []
    client = CurrencyQuoteClient("USD-BRL", validate=False)
    client.repository = CurrencyAPI(http)
    with pytest.raises(NoDataForDateError):
        client.get_history_quote("2024-06-01")
    client.close()


def test_history_404_window_does_not_discard_other_windows():
    http = Mock()
    http.get.side_effect = [
        CurrencyAPIError("not archived", 404),
        [entry("2025-01-01")],
    ]
    result = CurrencyAPI(http).get_history(
        "USD-BRL", date(2024, 1, 1), date(2025, 1, 1)
    )
    assert len(result) == 1


def test_parities_cache_and_schema():
    http = Mock()
    http.get.return_value = {"USD-BRL": "Dólar/Real"}
    validator = CurrencyValidatorAPI(http)
    assert validator.available_pairs() == {"USD-BRL"}
    assert validator.available_pairs() == {"USD-BRL"}
    http.get.assert_called_once()
    other = CurrencyValidatorAPI(http)
    http.get.return_value = []
    with pytest.raises(CurrencyAPIError):
        other.available_pairs()


def test_parities_cache_expires(monkeypatch):
    from currency_quote.adapters.outbound import currency_validator_api as module

    clock = iter([1, 2, 3])
    monkeypatch.setattr(module, "monotonic", lambda: next(clock))
    http = Mock()
    http.get.side_effect = [{"USD-BRL": "USD/BRL"}, {"EUR-BRL": "EUR/BRL"}]
    validator = CurrencyValidatorAPI(http, ttl_seconds=1)
    assert validator.available_pairs() == {"USD-BRL"}
    assert validator.available_pairs() == {"EUR-BRL"}
    http.get.assert_called_with("https://economia.awesomeapi.com.br/json/available")


def test_invalid_history_entry_is_typed():
    http = Mock()
    http.get.return_value = [{"timestamp": "bad", "bid": "5.1", "ask": "5.2"}]
    with pytest.raises(CurrencyAPIError, match="Malformed quote"):
        CurrencyAPI(http).get_history("USD-BRL", date(2024, 6, 3), date(2024, 6, 3))


def test_overflowing_history_timestamp_is_typed():
    http = Mock()
    http.get.return_value = [{"timestamp": "9" * 100, "bid": "5.1", "ask": "5.2"}]
    with pytest.raises(CurrencyAPIError, match="Malformed trading timestamp"):
        CurrencyAPI(http).get_history("USD-BRL", date(2024, 6, 3), date(2024, 6, 3))
