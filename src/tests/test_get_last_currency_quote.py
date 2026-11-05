# src/tests/test_get_last_currency_quote.py
from unittest.mock import patch

import pytest
from currency_quote.application.use_cases.get_last_currency_quote import (
    GetLastCurrencyQuoteUseCase,
)
from currency_quote.domain.entities.currency import CurrencyQuote, CurrencyObject


def make_quote(currency_pair, bid):
    code, quote_code = currency_pair.split("-")
    return CurrencyQuote(
        currency_pair=currency_pair,
        currency_pair_name=f"{code}/{quote_code}",
        base_currency_code=code,
        quote_currency_code=quote_code,
        quote_timestamp=1614024000,
        bid_price=bid,
        ask_price=bid + 0.01,
    )


@patch(
    "currency_quote.application.use_cases.get_last_currency_quote.GetCurrencyQuoteService"
)
@patch(
    "currency_quote.domain.services.get_currency_quote.ValidateCurrencyUseCase.execute"
)
def test_valid_currency_mocked(mock_validate, mock_service):
    """Test getting last quote with valid currencies using mocked service."""
    mock_validate.return_value = CurrencyObject(["USD-BRL", "EUR-BRL"])
    mock_quotes = [make_quote("USD-BRL", 5.0876), make_quote("EUR-BRL", 6.0876)]
    mock_service.return_value.last.return_value = mock_quotes

    result = GetLastCurrencyQuoteUseCase.execute(CurrencyObject(["USD-BRL", "EUR-BRL"]))

    assert len(result) == 2
    assert result[0].currency_pair == "USD-BRL"
    assert result[1].currency_pair == "EUR-BRL"
    mock_service.assert_called_once()
    factory_arg = mock_service.call_args.kwargs["currency_repository"]
    assert factory_arg(CurrencyObject(["USD-BRL"])) is not None


@patch(
    "currency_quote.application.use_cases.get_last_currency_quote.GetCurrencyQuoteService"
)
@patch(
    "currency_quote.domain.services.get_currency_quote.ValidateCurrencyUseCase.execute"
)
def test_partial_valid_currency(mock_validate, mock_service):
    """Validator filters invalid currencies; only valid ones reach the repository."""
    mock_validate.return_value = CurrencyObject(["USD-BRL", "EUR-BRL"])
    mock_service.return_value.last.return_value = [make_quote("USD-BRL", 5.0876)]

    result = GetLastCurrencyQuoteUseCase.execute(
        CurrencyObject(["USD-BRL", "EUR-BRL", "AAA-BBB"])
    )

    assert all(isinstance(item, CurrencyQuote) for item in result)
    assert all(item.currency_pair in ["USD-BRL", "EUR-BRL"] for item in result)


@patch(
    "currency_quote.domain.services.get_currency_quote.ValidateCurrencyUseCase.execute"
)
def test_all_invalid_currencies(mock_validate):
    """Test behavior when all currencies are invalid."""
    mock_validate.side_effect = ValueError("All params are invalid.")

    with pytest.raises(ValueError, match="All params are invalid."):
        GetLastCurrencyQuoteUseCase.execute(CurrencyObject(["AAA-BBB", "XXX-YYY"]))


@patch(
    "currency_quote.application.use_cases.get_last_currency_quote.GetCurrencyQuoteService"
)
@patch(
    "currency_quote.domain.services.get_currency_quote.ValidateCurrencyUseCase.execute"
)
def test_api_error_handling_mocked(mock_validate, mock_service):
    """Test handling of API errors using mocked service."""
    mock_validate.return_value = CurrencyObject(["USD-BRL"])
    mock_service.return_value.last.side_effect = Exception("API Connection Error")

    with pytest.raises(Exception, match="API Connection Error"):
        GetLastCurrencyQuoteUseCase.execute(CurrencyObject(["USD-BRL"]))


@patch(
    "currency_quote.application.use_cases.get_last_currency_quote.GetCurrencyQuoteService"
)
def test_skip_validation_avoids_validator(mock_service):
    """With validate=False, ValidateCurrencyUseCase must never execute."""
    mock_service.return_value.last.return_value = [make_quote("USD-BRL", 5.0876)]

    result = GetLastCurrencyQuoteUseCase.execute(
        CurrencyObject(["USD-BRL"]), validate=False
    )

    assert result[0].currency_pair == "USD-BRL"
    assert mock_service.call_args.kwargs["validate"] is False
