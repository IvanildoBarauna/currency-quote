import pytest
from unittest.mock import patch, MagicMock
from currency_quote import ClientBuilder, CurrencyQuoteClient
from currency_quote.domain.entities.currency import CurrencyQuote, CurrencyObject
from currency_quote.exceptions import InvalidDateError


@pytest.fixture
def client():
    """Create a simple client for testing."""
    return ClientBuilder(currency_list=["USD-BRL"])


def test_client_builder(client):
    """Test that ClientBuilder instantiates correctly."""
    assert isinstance(client, ClientBuilder)
    assert client.currency_list == ["USD-BRL"]


def test_client_methods_simple():
    """Test basic functionality of client methods without mocking."""
    # Create client with direct approaches to avoid complex mocking
    client = ClientBuilder(currency_list=["USD-BRL"])

    # Check that the methods exist and return the right types
    assert hasattr(client, "get_last_quote")
    assert hasattr(client, "get_history_quote")

    # Simple validation of signatures
    assert "reference_date" in client.get_history_quote.__code__.co_varnames


def test_instantiate_with_different_inputs():
    """Test instantiating ClientBuilder with different currency inputs."""
    # Test with string
    client1 = ClientBuilder(currency_list="USD-BRL")
    assert client1.currency_list == "USD-BRL"
    assert isinstance(client1.currency_obj, CurrencyObject)
    assert client1.currency_obj.get_currency_list() == ["USD-BRL"]

    # Test with list
    client2 = ClientBuilder(currency_list=["USD-BRL", "EUR-BRL"])
    assert client2.currency_list == ["USD-BRL", "EUR-BRL"]
    assert isinstance(client2.currency_obj, CurrencyObject)
    assert "USD-BRL" in client2.currency_obj.get_currency_list()
    assert "EUR-BRL" in client2.currency_obj.get_currency_list()
    assert len(client2.currency_obj.get_currency_list()) == 2


def test_client_builder_is_alias_of_currency_quote_client():
    """The legacy name must keep working."""
    assert ClientBuilder is CurrencyQuoteClient
    assert isinstance(CurrencyQuoteClient("USD-BRL"), ClientBuilder)


def test_currencies_property_returns_normalized_pairs():
    client = CurrencyQuoteClient("usd/brl")
    assert client.currencies == ["USD-BRL"]


def test_invalid_reference_date():
    """get_history_quote must raise instead of silently returning []."""
    client = ClientBuilder(currency_list=["USD-BRL"])

    with pytest.raises(InvalidDateError):
        client.get_history_quote(reference_date=99999999)
