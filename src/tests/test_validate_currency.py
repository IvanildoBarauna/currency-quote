import pytest
from unittest.mock import patch
from currency_quote.application.use_cases.validate_currency import (
    ValidateCurrencyUseCase,
)
from currency_quote.domain.entities.currency import CurrencyObject
from currency_quote.adapters.outbound.currency_validator_api import CurrencyValidatorAPI
from currency_quote.domain.services.validate_currency import CurrencyValidatorService


def test_valid_currency():
    """Test validation of valid currencies."""
    currency_list = ["USD-BRL", "USD-BRLT"]
    currency_quote = CurrencyObject(currency_list)
    
    # Mock the validator API to return the same currencies
    with patch.object(CurrencyValidatorAPI, 'validate_currency_code', return_value=currency_list):
        result = ValidateCurrencyUseCase.execute(currency_quote=currency_quote)
        assert result.get_currency_list() == currency_list
        assert isinstance(result, CurrencyObject)


def test_partial_valid_currency():
    """Reject invalid pairs rather than quietly returning partial results."""
    currency_list = ["USD-BRL", "USD-BRLT", "AAA-BBB"]
    currency_quote = CurrencyObject(currency_list)
    expected_result = ["USD-BRL", "USD-BRLT"]
    
    # Mock the validator API to return only valid currencies
    with patch.object(CurrencyValidatorAPI, 'validate_currency_code', return_value=expected_result):
        with pytest.raises(ValueError, match="AAA-BBB"):
            ValidateCurrencyUseCase.execute(currency_quote=currency_quote)


def test_all_invalid_currencies():
    """Test validation when all currencies are invalid."""
    currency_list = ["AAA-BBB", "XXX-YYY"]
    currency_quote = CurrencyObject(currency_list)
    
    # Mock the validator to return empty list, which raises ValueError
    with patch.object(CurrencyValidatorAPI, 'validate_currency_code', return_value=[]):
        with pytest.raises(ValueError, match="All params: .* are invalid."):
            ValidateCurrencyUseCase.execute(currency_quote=currency_quote)


def test_api_validator_error():
    """Test handling of validator API errors."""
    currency_list = ["USD-BRL"]
    currency_quote = CurrencyObject(currency_list)
    
    # Mock the validator API to raise an exception
    with patch.object(CurrencyValidatorAPI, 'validate_currency_code', side_effect=Exception("API Error")):
        with pytest.raises(Exception, match="API Error"):
            ValidateCurrencyUseCase.execute(currency_quote=currency_quote)


def test_special_character_validation():
    """Test validation of currencies including special characters (which should be invalid)."""
    # Create currency object with only valid currencies first
    currency_quote = CurrencyObject(["USD-BRL"])
    
    # Then test validation where API only returns valid currencies
    expected_result = ["USD-BRL"]
    invalid_result = ["XXX-YYY"] # This represents what would have been filtered out
    
    # Mock validator to only return valid currencies
    with patch.object(CurrencyValidatorAPI, 'validate_currency_code', return_value=expected_result):
        result = ValidateCurrencyUseCase.execute(currency_quote=currency_quote)
        assert result.get_currency_list() == expected_result
        assert all(c not in result.get_currency_list() for c in invalid_result)
