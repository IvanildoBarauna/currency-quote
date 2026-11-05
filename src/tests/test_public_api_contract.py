"""Exercise the public client with the provider boundary mocked, not the use case."""

from datetime import datetime
from unittest.mock import patch

import pytest

from currency_quote import ClientBuilder
from currency_quote.adapters.outbound.currency_validator_api import CurrencyValidatorAPI
from currency_quote.domain.entities.currency import CurrencyQuote


def test_public_latest_returns_decimal_strings(mock_currency_api_response):
    with patch.object(
        CurrencyValidatorAPI, "validate_currency_code", return_value=["USD-BRL"]
    ):
        with patch(
            "currency_quote.adapters.outbound.currency_api.ClientBuilder"
        ) as builder:
            builder.return_value.get_api_data.return_value = mock_currency_api_response
            result = ClientBuilder("USD-BRL").get_last_quote()

    assert len(result) == 1
    assert result[0]["currency_pair"] == "USD-BRL"
    assert result[0]["bid_price"] == "5.0876"
    assert result[0]["ask_price"] == "5.0891"
    assert isinstance(result[0]["quote_extracted_at"], int)


def test_public_history_returns_same_price_types(mock_currency_history_api_response):
    with patch.object(
        CurrencyValidatorAPI, "validate_currency_code", return_value=["USD-BRL"]
    ):
        with patch(
            "currency_quote.adapters.outbound.currency_api.ClientBuilder"
        ) as builder:
            builder.return_value.get_api_data.return_value = (
                mock_currency_history_api_response
            )
            result = ClientBuilder("USD-BRL").get_history_quote(20220621)

    assert len(result) == 1
    assert result[0]["bid_price"] == "5.0876"
    assert result[0]["ask_price"] == "5.0891"


def test_missing_history_is_not_an_invalid_date():
    with patch.object(
        CurrencyValidatorAPI, "validate_currency_code", return_value=["USD-BRL"]
    ):
        with patch(
            "currency_quote.adapters.outbound.currency_api.ClientBuilder"
        ) as builder:
            builder.return_value.get_api_data.return_value = []
            with pytest.raises(LookupError, match="USD-BRL on 20220621"):
                ClientBuilder("USD-BRL").get_history_quote(20220621)


def test_partial_validation_does_not_silently_drop_pairs():
    with patch.object(
        CurrencyValidatorAPI, "validate_currency_code", return_value=["USD-BRL"]
    ):
        with patch(
            "currency_quote.adapters.outbound.currency_api.ClientBuilder"
        ) as builder:
            with pytest.raises(ValueError, match="AAA-BBB"):
                ClientBuilder(["USD-BRL", "AAA-BBB"]).get_last_quote()
            builder.assert_not_called()


@pytest.mark.parametrize(
    "invalid", [20220230, 20221301, 2022011, 20220101.0, True, 99999999]
)
def test_invalid_history_dates_fail_before_any_network_call(invalid):
    with patch.object(CurrencyValidatorAPI, "validate_currency_code") as validator:
        with pytest.raises(ValueError, match="reference_date"):
            ClientBuilder("USD-BRL").get_history_quote(invalid)
        validator.assert_not_called()


def test_extraction_time_is_computed_for_each_quote(monkeypatch):
    from currency_quote.domain.entities import currency

    class FirstClock:
        @staticmethod
        def now():
            return datetime.fromtimestamp(1000000000)

    class SecondClock:
        @staticmethod
        def now():
            return datetime.fromtimestamp(1000000010)

    kwargs = dict(
        currency_pair="USD-BRL",
        currency_pair_name="USD/BRL",
        base_currency_code="USD",
        quote_currency_code="BRL",
        quote_timestamp=1000000000,
        bid_price="1.23",
        ask_price="1.24",
    )
    monkeypatch.setattr(currency, "datetime", FirstClock)
    first = CurrencyQuote(**kwargs)
    monkeypatch.setattr(currency, "datetime", SecondClock)
    second = CurrencyQuote(**kwargs)

    assert second.quote_extracted_at - first.quote_extracted_at == 10
