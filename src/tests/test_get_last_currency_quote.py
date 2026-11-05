import pytest
from unittest.mock import patch, MagicMock
from currency_quote.application.use_cases.get_last_currency_quote import (
    GetLastCurrencyQuoteUseCase,
)
from currency_quote.domain.entities.currency import CurrencyQuote, CurrencyObject
from currency_quote.domain.services.get_currency_quote import GetCurrencyQuoteService


def test_valid_currency_mocked():
    """Test getting last quote with valid currencies using mocked repository."""
    # Create mock quotes
    mock_quotes = [
        CurrencyQuote(
            currency_pair="USD-BRL",
            currency_pair_name="Dólar Americano/Real Brasileiro",
            base_currency_code="USD",
            quote_currency_code="BRL",
            quote_timestamp=1614024000,
            bid_price=5.0876,
            ask_price=5.0891,
        ),
        CurrencyQuote(
            currency_pair="EUR-BRL",
            currency_pair_name="Euro/Real Brasileiro",
            base_currency_code="EUR",
            quote_currency_code="BRL",
            quote_timestamp=1614024000,
            bid_price=6.0876,
            ask_price=6.0891,
        ),
    ]

    # Mock the currency repository
    mock_repository = MagicMock()
    mock_repository.return_value.get_last_quote.return_value = mock_quotes

    # Mock the ValidateCurrencyUseCase to return valid currencies
    valid_currencies = CurrencyObject(["USD-BRL", "EUR-BRL"])

    with patch(
        "currency_quote.domain.services.get_currency_quote.ValidateCurrencyUseCase.execute",
        return_value=valid_currencies,
    ):
        with patch(
            "currency_quote.application.use_cases.get_last_currency_quote.GetCurrencyQuoteService"
        ) as mock_service:
            # Configure the mock service
            mock_service_instance = MagicMock()
            mock_service_instance.last.return_value = mock_quotes
            mock_service.return_value = mock_service_instance

            # Test data
            currency_list = ["USD-BRL", "EUR-BRL"]
            currency_quote = CurrencyObject(currency_list)

            # Call the function
            result = GetLastCurrencyQuoteUseCase.execute(currency_quote)

            # Verify results
            assert len(result) == 2
            assert result[0].currency_pair == "USD-BRL"
            assert result[1].currency_pair == "EUR-BRL"

            # Verify the mock service was called
            mock_service.assert_called_once()


def test_partial_valid_currency():
    """Test getting last quote with a mix of valid and invalid currencies."""
    # Create mock quotes for valid currencies only
    mock_quotes = [
        CurrencyQuote(
            currency_pair="USD-BRL",
            currency_pair_name="Dólar Americano/Real Brasileiro",
            base_currency_code="USD",
            quote_currency_code="BRL",
            quote_timestamp=1614024000,
            bid_price=5.0876,
            ask_price=5.0891,
        ),
        CurrencyQuote(
            currency_pair="EUR-BRL",
            currency_pair_name="Euro/Real Brasileiro",
            base_currency_code="EUR",
            quote_currency_code="BRL",
            quote_timestamp=1614024000,
            bid_price=6.0876,
            ask_price=6.0891,
        ),
    ]

    # Mock the currency validator to filter invalid currencies
    valid_currencies = CurrencyObject(["USD-BRL", "EUR-BRL"])

    with patch(
        "currency_quote.domain.services.get_currency_quote.ValidateCurrencyUseCase.execute",
        return_value=valid_currencies,
    ):
        with patch(
            "currency_quote.application.use_cases.get_last_currency_quote.GetCurrencyQuoteService"
        ) as mock_service:
            # Configure the mock service
            mock_service_instance = MagicMock()
            mock_service_instance.last.return_value = mock_quotes
            mock_service.return_value = mock_service_instance

            # Test data with one invalid currency
            currency_list = ["USD-BRL", "EUR-BRL", "AAA-BBB"]
            currency_quote = CurrencyObject(currency_list)

            # Call the function
            result = GetLastCurrencyQuoteUseCase.execute(currency_quote)

            # Verify results
            assert len(result) == 2
            for item in result:
                assert isinstance(item, CurrencyQuote)
                assert item.currency_pair in ["USD-BRL", "EUR-BRL"]


def test_all_invalid_currencies():
    """Test behavior when all currencies are invalid."""
    # Mock the validator to raise ValueError for all invalid currencies
    with patch(
        "currency_quote.domain.services.get_currency_quote.ValidateCurrencyUseCase.execute",
        side_effect=ValueError("All params are invalid."),
    ):
        # Test data with all invalid currencies
        currency_list = ["AAA-BBB", "XXX-YYY"]
        currency_quote = CurrencyObject(currency_list)

        # Verify that ValueError is raised
        with pytest.raises(ValueError, match="All params are invalid."):
            GetLastCurrencyQuoteUseCase.execute(currency_quote)


def test_api_error_handling_mocked():
    """Test handling of API errors using mocked repository."""
    # Mock the GetCurrencyQuoteService to simulate an API error
    valid_currencies = CurrencyObject(["USD-BRL"])

    with patch(
        "currency_quote.domain.services.get_currency_quote.ValidateCurrencyUseCase.execute",
        return_value=valid_currencies,
    ):
        with patch(
            "currency_quote.application.use_cases.get_last_currency_quote.GetCurrencyQuoteService"
        ) as mock_service:
            # Configure the mock to raise an exception when get_last_quote is called
            mock_service_instance = MagicMock()
            mock_service_instance.last.side_effect = Exception("API Connection Error")
            mock_service.return_value = mock_service_instance

            # Test data
            currency_quote = CurrencyObject(["USD-BRL"])

            # Verify that the exception is raised
            with pytest.raises(Exception, match="API Connection Error"):
                GetLastCurrencyQuoteUseCase.execute(currency_quote)
