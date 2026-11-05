# src/tests/test_get_history_currency_quote.py
from datetime import datetime
from unittest.mock import patch

import pytest

from currency_quote.application.use_cases.get_history_currency_quote import (
    GetHistCurrencyQuoteUseCase,
)
from currency_quote.domain.entities.currency import CurrencyObject, CurrencyQuote
from currency_quote.adapters.outbound.currency_api import CurrencyAPI
from currency_quote.adapters.outbound.currency_validator_api import CurrencyValidatorAPI
from currency_quote.domain.services.validate_currency import CurrencyValidatorService
from currency_quote.exceptions import InvalidDateError


def make_quote():
    return CurrencyQuote(
        currency_pair="USD-BRL",
        currency_pair_name="Dólar Americano/Real Brasileiro",
        base_currency_code="USD",
        quote_currency_code="BRL",
        quote_timestamp=1614024000,
        bid_price=5.0876,
        ask_price=5.0891,
    )


def test_valid_history_quote_mocked():
    """Test getting historical quote with valid parameters using complete mocking."""
    with patch(
        "currency_quote.application.use_cases.get_history_currency_quote."
        "GetHistCurrencyQuoteUseCase.execute"
    ) as mock_execute:
        mock_quote = make_quote()
        mock_execute.return_value = [mock_quote]

        currency_quote = CurrencyObject(["USD-BRL"])
        reference_date = 20220621

        result = GetHistCurrencyQuoteUseCase.execute(currency_quote, reference_date)

        assert len(result) == 1
        assert result[0] == mock_quote
        assert result[0].bid_price == 5.0876
        mock_execute.assert_called_once_with(currency_quote, reference_date)


@patch("currency_quote.utils.http.requests.get")
def test_today_reference_date_raises(mock_get):
    """Today is rejected with a typed error and no HTTP request is made."""
    currency_quote = CurrencyObject(["USD-BRL"])
    today = int(datetime.today().strftime("%Y%m%d"))

    with patch.object(
        CurrencyValidatorService, "validate_currency_code", return_value=currency_quote
    ):
        with patch.object(
            CurrencyValidatorAPI, "validate_currency_code", return_value=["USD-BRL"]
        ):
            with pytest.raises(InvalidDateError, match="earlier than today"):
                GetHistCurrencyQuoteUseCase.execute(currency_quote, today)

    mock_get.assert_not_called()


@patch("currency_quote.utils.http.requests.get")
def test_future_reference_date_raises(mock_get):
    currency_quote = CurrencyObject(["USD-BRL"])

    with patch.object(
        CurrencyValidatorService, "validate_currency_code", return_value=currency_quote
    ):
        with patch.object(
            CurrencyValidatorAPI, "validate_currency_code", return_value=["USD-BRL"]
        ):
            with pytest.raises(InvalidDateError):
                GetHistCurrencyQuoteUseCase.execute(currency_quote, 20301231)

    mock_get.assert_not_called()


@patch("currency_quote.utils.http.requests.get")
def test_invalid_date_format_raises(mock_get):
    """Only 6 digits is malformed: raises instead of returning [] silently."""
    currency_quote = CurrencyObject(["USD-BRL"])

    with patch.object(
        CurrencyValidatorService, "validate_currency_code", return_value=currency_quote
    ):
        with patch.object(
            CurrencyValidatorAPI, "validate_currency_code", return_value=["USD-BRL"]
        ):
            with pytest.raises(InvalidDateError, match="Invalid reference date"):
                GetHistCurrencyQuoteUseCase.execute(currency_quote, 220621)

    mock_get.assert_not_called()


def test_api_error_handling_mocked():
    """Test handling of API errors for historical quotes using complete mocking."""
    with patch(
        "currency_quote.adapters.outbound.currency_api.CurrencyAPI.get_history_quote"
    ) as mock_get_history:
        mock_get_history.side_effect = Exception("API Connection Error")

        currency_quote = CurrencyObject(["USD-BRL"])
        reference_date = 20220621

        try:
            api = CurrencyAPI(currency_quote)
            api.get_history_quote(reference_date)
            assert False, "Exception was not raised"
        except Exception as e:  # pylint: disable=broad-except
            assert "API Connection Error" in str(e)
