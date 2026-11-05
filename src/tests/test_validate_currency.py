# src/tests/test_validate_currency.py
from unittest.mock import patch

import pytest
from currency_quote.application.use_cases.validate_currency import (
    ValidateCurrencyUseCase,
)
from currency_quote.adapters.outbound.currency_validator_api import (
    CurrencyValidatorAPI,
)
from currency_quote.domain.entities.currency import CurrencyObject
from currency_quote.exceptions import CurrencyAPIError


def test_valid_currency():
    """Test validation of valid currencies."""
    currency_list = ["USD-BRL", "USD-BRLT"]
    currency_quote = CurrencyObject(currency_list)

    with patch.object(
        CurrencyValidatorAPI, "validate_currency_code", return_value=currency_list
    ):
        result = ValidateCurrencyUseCase.execute(currency_quote=currency_quote)
        assert result.get_currency_list() == currency_list
        assert isinstance(result, CurrencyObject)


def test_partial_valid_currency():
    """Test validation with some invalid currencies."""
    currency_list = ["USD-BRL", "USD-BRLT", "AAA-BBB"]
    currency_quote = CurrencyObject(currency_list)
    expected_result = ["USD-BRL", "USD-BRLT"]

    with patch.object(
        CurrencyValidatorAPI, "validate_currency_code", return_value=expected_result
    ):
        result = ValidateCurrencyUseCase.execute(currency_quote=currency_quote)
        assert result.get_currency_list() == expected_result
        assert isinstance(result, CurrencyObject)


def test_all_invalid_currencies():
    """Test validation when all currencies are invalid."""
    currency_list = ["AAA-BBB", "XXX-YYY"]
    currency_quote = CurrencyObject(currency_list)

    with patch.object(CurrencyValidatorAPI, "validate_currency_code", return_value=[]):
        with pytest.raises(ValueError, match="All params: .* are invalid."):
            ValidateCurrencyUseCase.execute(currency_quote=currency_quote)


def test_api_validator_error():
    """Test handling of validator API errors."""
    currency_list = ["USD-BRL"]
    currency_quote = CurrencyObject(currency_list)

    with patch.object(
        CurrencyValidatorAPI,
        "validate_currency_code",
        side_effect=Exception("API Error"),
    ):
        with pytest.raises(Exception, match="API Error"):
            ValidateCurrencyUseCase.execute(currency_quote=currency_quote)


@patch("currency_quote.adapters.outbound.currency_validator_api.get_json")
def test_validator_hits_api_once_and_caches(mock_get_json, mock_validator_api_response):
    """The parities list is cached: repeated calls must trigger a single HTTP request."""
    mock_get_json.return_value = {pair: "name" for pair in mock_validator_api_response}

    first = CurrencyValidatorAPI(CurrencyObject(["USD-BRL"])).validate_currency_code()
    second = CurrencyValidatorAPI(CurrencyObject(["EUR-BRL"])).validate_currency_code()

    assert first == ["USD-BRL"]
    assert second == ["EUR-BRL"]
    assert mock_get_json.call_count == 1


@patch("currency_quote.adapters.outbound.currency_validator_api.get_json")
def test_validator_malformed_parities_payload_raises(mock_get_json):
    mock_get_json.return_value = ["unexpected", "list"]
    with pytest.raises(CurrencyAPIError, match="expected a JSON object"):
        CurrencyValidatorAPI(CurrencyObject(["USD-BRL"])).validate_currency_code()
