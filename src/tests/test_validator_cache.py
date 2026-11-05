from unittest.mock import patch

import pytest

import currency_quote.adapters.outbound.currency_validator_api as validator_module
from currency_quote.adapters.outbound.currency_validator_api import (
    CurrencyValidatorAPI,
    clear_available_parities_cache,
)
from currency_quote.domain.entities.currency import CurrencyObject
from currency_quote.exceptions import QuoteFetchError

TARGET = "currency_quote.adapters.outbound.currency_validator_api.ClientBuilder"


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_available_parities_cache()
    yield
    clear_available_parities_cache()


def test_filters_unsupported_pairs(mock_validator_api_response):
    validator = CurrencyValidatorAPI(CurrencyObject(["USD-BRL", "AAA-BBB"]))

    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = mock_validator_api_response
        assert validator.validate_currency_code() == ["USD-BRL"]


def test_available_parities_are_cached_across_calls(mock_validator_api_response):
    """Regression: every quote used to trigger a second HTTP round-trip."""
    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = mock_validator_api_response

        for _ in range(5):
            CurrencyValidatorAPI(CurrencyObject(["USD-BRL"])).validate_currency_code()

        assert client.call_count == 1


def test_clear_cache_forces_refetch(mock_validator_api_response):
    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = mock_validator_api_response

        CurrencyValidatorAPI(CurrencyObject(["USD-BRL"])).validate_currency_code()
        clear_available_parities_cache()
        CurrencyValidatorAPI(CurrencyObject(["USD-BRL"])).validate_currency_code()

        assert client.call_count == 2


def test_expired_cache_is_refetched(mock_validator_api_response):
    with patch(TARGET) as client:
        client.return_value.get_api_data.return_value = mock_validator_api_response

        CurrencyValidatorAPI(CurrencyObject(["USD-BRL"])).validate_currency_code()

        # Simulate the TTL elapsing
        validator_module._cache._fetched_at -= (
            validator_module.API.AVAILABLE_PARITIES_TTL_SECONDS + 1
        )

        CurrencyValidatorAPI(CurrencyObject(["USD-BRL"])).validate_currency_code()
        assert client.call_count == 2


def test_transport_failure_is_wrapped():
    with patch(TARGET) as client:
        client.return_value.get_api_data.side_effect = RuntimeError("down")
        with pytest.raises(QuoteFetchError, match="available currency pairs"):
            CurrencyValidatorAPI(CurrencyObject(["USD-BRL"])).validate_currency_code()
