# src/tests/test_lib_controller.py
"""Backward-compatibility facade tests (v5 style dict results)."""
from unittest.mock import patch

import pytest

from currency_quote import ClientBuilder
from currency_quote.domain.entities.currency import CurrencyQuote, CurrencyObject
from currency_quote.exceptions import InvalidDateError


def make_quote(pair="USD-BRL"):
    code, quote_code = pair.split("-")
    return CurrencyQuote(
        currency_pair=pair,
        currency_pair_name=f"{code}/{quote_code}",
        base_currency_code=code,
        quote_currency_code=quote_code,
        quote_timestamp=1614024000,
        bid_price=5.0876,
        ask_price=5.0891,
    )


@pytest.fixture
def usd_client():
    """Create a simple client for testing."""
    return ClientBuilder(currency_list=["USD-BRL"])


def test_client_builder(usd_client):
    """Test that ClientBuilder instantiates correctly."""
    assert isinstance(usd_client, ClientBuilder)
    assert usd_client.currency_list == ["USD-BRL"]


def test_client_methods_simple():
    """Test basic functionality of client methods without mocking."""
    builder = ClientBuilder(currency_list=["USD-BRL"])

    assert hasattr(builder, "get_last_quote")
    assert hasattr(builder, "get_history_quote")
    assert "reference_date" in builder.get_history_quote.__code__.co_varnames


def test_instantiate_with_different_inputs():
    """Test instantiating ClientBuilder with different currency inputs."""
    client1 = ClientBuilder(currency_list="USD-BRL")
    assert client1.currency_list == "USD-BRL"
    assert isinstance(client1.currency_obj, CurrencyObject)
    assert client1.currency_obj.get_currency_list() == ["USD-BRL"]

    client2 = ClientBuilder(currency_list=["USD-BRL", "EUR-BRL"])
    assert client2.currency_list == ["USD-BRL", "EUR-BRL"]
    assert isinstance(client2.currency_obj, CurrencyObject)
    assert len(client2.currency_obj.get_currency_list()) == 2


def test_invalid_reference_date_raises():
    """Invalid dates now raise a typed error instead of returning [] silently."""
    client = ClientBuilder(currency_list=["USD-BRL"])
    with pytest.raises(InvalidDateError):
        client.get_history_quote(reference_date=99999999)


@patch("currency_quote.adapters.inbound.lib_controller.GetLastCurrencyQuoteUseCase")
def test_get_last_quote_returns_normalized_dicts(mock_use_case):
    mock_use_case.execute.return_value = [make_quote()]
    result = ClientBuilder(currency_list=["USD-BRL"]).get_last_quote()

    assert isinstance(result, list)
    assert all(isinstance(item, dict) for item in result)
    assert result[0]["currency_pair"] == "USD-BRL"
    assert result[0]["bid_price"] == 5.0876  # normalized to float
    assert "high_price" in result[0]


@patch("currency_quote.adapters.inbound.lib_controller.GetHistCurrencyQuoteUseCase")
def test_get_history_quote_returns_normalized_dicts(mock_use_case):
    mock_use_case.execute.return_value = [make_quote()]
    result = ClientBuilder(currency_list=["USD-BRL"]).get_history_quote(
        reference_date=20220621
    )

    assert isinstance(result, list)
    assert result[0]["bid_price"] == 5.0876
    assert mock_use_case.execute.call_args.kwargs["reference_date"] == 20220621
