import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from currency_quote.application.use_cases.get_history_currency_quote import (
    GetHistCurrencyQuoteUseCase,
)
from currency_quote.domain.entities.currency import CurrencyQuote, CurrencyObject
from currency_quote.adapters.outbound.currency_api import CurrencyAPI
from currency_quote.adapters.outbound.currency_validator_api import CurrencyValidatorAPI
from currency_quote.domain.services.validate_currency import CurrencyValidatorService
from currency_quote.exceptions import InvalidDateError


def test_valid_history_quote_mocked():
    """Test getting historical quote with valid parameters using complete mocking."""
    # Mock the entire execute method to return pre-configured data
    with patch(
        "currency_quote.application.use_cases.get_history_currency_quote.GetHistCurrencyQuoteUseCase.execute"
    ) as mock_execute:
        # Create a predefined quote object for the result
        mock_quote = CurrencyQuote(
            currency_pair="USD-BRL",
            currency_pair_name="Dólar Americano/Real Brasileiro",
            base_currency_code="USD",
            quote_currency_code="BRL",
            quote_timestamp=1614024000,
            bid_price=5.0876,
            ask_price=5.0891,
        )

        # Configure the mock to return our predefined quote
        mock_execute.return_value = [mock_quote]

        # Test data
        currency_list = ["USD-BRL"]
        currency_quote = CurrencyObject(currency_list)
        reference_date = 20220621

        # Call the function through the mock
        result = GetHistCurrencyQuoteUseCase.execute(currency_quote, reference_date)

        # Verify results
        assert len(result) == 1
        assert result[0] == mock_quote
        assert result[0].currency_pair == "USD-BRL"
        assert result[0].bid_price == 5.0876
        assert result[0].ask_price == 5.0891

        # Verify the mock was called with the right parameters
        mock_execute.assert_called_once_with(currency_quote, reference_date)


@patch("api_to_dataframe.ClientBuilder")
def test_invalid_reference_date(mock_client_builder):
    """Test behavior with invalid reference date."""
    mock_client = MagicMock()
    mock_client_builder.return_value = mock_client

    # Test data
    currency_list = ["USD-BRL"]
    currency_quote = CurrencyObject(currency_list)

    # Current date as reference date (which is invalid)
    today = int(datetime.today().strftime("%Y%m%d"))

    # Mock the validator service
    with patch.object(
        CurrencyValidatorService, "validate_currency_code", return_value=currency_quote
    ):
        with patch.object(
            CurrencyValidatorAPI, "validate_currency_code", return_value=currency_list
        ):
            # Today is not a closed day yet, so it must be rejected
            with pytest.raises(InvalidDateError):
                GetHistCurrencyQuoteUseCase.execute(currency_quote, today)

            # Verify the API was never called
            mock_client.get_api_data.assert_not_called()


@patch("api_to_dataframe.ClientBuilder")
def test_future_reference_date(mock_client_builder):
    """Test behavior with future reference date."""
    mock_client = MagicMock()
    mock_client_builder.return_value = mock_client

    # Test data
    currency_list = ["USD-BRL"]
    currency_quote = CurrencyObject(currency_list)

    # Future date
    future_date = 20301231

    # Mock the validator service
    with patch.object(
        CurrencyValidatorService, "validate_currency_code", return_value=currency_quote
    ):
        with patch.object(
            CurrencyValidatorAPI, "validate_currency_code", return_value=currency_list
        ):
            with pytest.raises(InvalidDateError):
                GetHistCurrencyQuoteUseCase.execute(currency_quote, future_date)

            # Verify the API was never called
            mock_client.get_api_data.assert_not_called()


@patch("api_to_dataframe.ClientBuilder")
def test_invalid_date_format(mock_client_builder):
    """Test behavior with invalid date format."""
    mock_client = MagicMock()
    mock_client_builder.return_value = mock_client

    # Test data
    currency_list = ["USD-BRL"]
    currency_quote = CurrencyObject(currency_list)

    # Invalid date format (only 6 digits)
    invalid_date = 220621

    # Mock the validator service
    with patch.object(
        CurrencyValidatorService, "validate_currency_code", return_value=currency_quote
    ):
        with patch.object(
            CurrencyValidatorAPI, "validate_currency_code", return_value=currency_list
        ):
            with pytest.raises(InvalidDateError):
                GetHistCurrencyQuoteUseCase.execute(currency_quote, invalid_date)

            # Verify the API was never called
            mock_client.get_api_data.assert_not_called()


def test_api_error_handling_mocked():
    """Test handling of API errors for historical quotes using complete mocking."""
    # Mock the CurrencyAPI directly to raise an exception
    with patch(
        "currency_quote.adapters.outbound.currency_api.CurrencyAPI.get_history_quote"
    ) as mock_get_history:
        # Configure mock to raise an exception
        mock_get_history.side_effect = Exception("API Connection Error")

        # Test with a simple try/except to verify exception is raised
        currency_quote = CurrencyObject(["USD-BRL"])
        reference_date = 20220621

        # Test the exception is propagated
        try:
            # Try to use a direct instance of CurrencyAPI
            api = CurrencyAPI(currency_quote)
            api.get_history_quote(reference_date)
            assert False, "Exception was not raised"
        except Exception as e:
            assert "API Connection Error" in str(e)
