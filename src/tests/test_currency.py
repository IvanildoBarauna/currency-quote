import pytest
from currency_quote.domain.entities.currency import CurrencyObject, CurrencyQuote
from datetime import datetime


def test_currency_object():
    """Test CurrencyObject with a valid currency list."""
    client = CurrencyObject(currency_list=["USD-BRL"])
    assert client.get_currency_list() == ["USD-BRL"]


def test_currency_object_with_str():
    """Test CurrencyObject with a valid currency string."""
    client = CurrencyObject(currency_list="USD-BRL")
    assert client.get_currency_list() == ["USD-BRL"]


def test_currency_object_with_multiple_currencies():
    """Test CurrencyObject with multiple valid currency pairs."""
    currency_list = ["USD-BRL", "EUR-BRL", "JPY-USD", "USD-BRLT"]
    client = CurrencyObject(currency_list=currency_list)
    assert client.get_currency_list() == currency_list
    assert len(client.get_currency_list()) == 4


def test_currency_object_with_empty_list():
    """Test CurrencyObject with an empty list (should raise ValueError)."""
    with pytest.raises(ValueError, match="Currency list is empty"):
        CurrencyObject(currency_list=[])


def test_currency_object_with_empty_str():
    """Test CurrencyObject with an empty string (should raise ValueError)."""
    with pytest.raises(ValueError):
        CurrencyObject(currency_list="")


def test_currency_object_with_invalid_currency_code():
    """Test CurrencyObject with invalid currency code (too short)."""
    with pytest.raises(ValueError, match="Each currency code must have 3 characters"):
        CurrencyObject(currency_list=["USD-BR"])


def test_currency_object_with_long_currency_code():
    """Test CurrencyObject with valid 4-character currency codes."""
    client = CurrencyObject(currency_list=["USD-BRLT"])
    assert client.get_currency_list() == ["USD-BRLT"]


def test_currency_object_with_invalid_types():
    """Test CurrencyObject with invalid type (should raise TypeError)."""
    with pytest.raises(TypeError, match="Currency list must be a list or a string"):
        CurrencyObject(currency_list=12312421312)


def test_currency_object_with_invalid_formats():
    """Test CurrencyObject with invalid format (should raise ValueError)."""
    currency_list = ["param1", "param2"]
    with pytest.raises(ValueError, match="Currency pair must be in the format"):
        CurrencyObject(currency_list)


def test_currency_object_with_mixed_valid_invalid():
    """Test CurrencyObject with a mix of valid and invalid formats (should raise ValueError)."""
    with pytest.raises(ValueError):
        CurrencyObject(currency_list=["USD-BRL", "INVALID"])


def test_currency_object_normalizes_case_and_separator():
    """Input is normalized so 'usd/brl' and 'USD-BRL' are equivalent."""
    assert CurrencyObject("usd/brl").get_currency_list() == ["USD-BRL"]
    assert CurrencyObject(" eur_brl ").get_currency_list() == ["EUR-BRL"]


def test_currency_object_removes_duplicates_preserving_order():
    client = CurrencyObject(["USD-BRL", "EUR-BRL", "usd-brl"])
    assert client.get_currency_list() == ["USD-BRL", "EUR-BRL"]


def test_currency_object_rejects_non_alphabetic_codes():
    with pytest.raises(ValueError):
        CurrencyObject(["US1-BRL"])


def test_currency_object_is_iterable_and_sized():
    client = CurrencyObject(["USD-BRL", "EUR-BRL"])
    assert len(client) == 2
    assert list(client) == ["USD-BRL", "EUR-BRL"]


def test_currency_object_equality():
    assert CurrencyObject("USD-BRL") == CurrencyObject("usd-brl")


def test_currency_quote_creation():
    """Test creation of CurrencyQuote object with valid data."""
    quote = CurrencyQuote(
        currency_pair="USD-BRL",
        currency_pair_name="Dólar Americano/Real Brasileiro",
        base_currency_code="USD",
        quote_currency_code="BRL",
        quote_timestamp=1614024000,
        bid_price=5.0876,
        ask_price=5.0891,
    )

    # Verify all attributes are set correctly
    assert quote.currency_pair == "USD-BRL"
    assert quote.currency_pair_name == "Dólar Americano/Real Brasileiro"
    assert quote.base_currency_code == "USD"
    assert quote.quote_currency_code == "BRL"
    assert quote.quote_timestamp == 1614024000
    assert quote.bid_price == 5.0876
    assert quote.ask_price == 5.0891
    assert quote.quote_extracted_at <= int(datetime.now().timestamp())
