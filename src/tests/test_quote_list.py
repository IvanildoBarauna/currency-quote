import json
import time

import pytest

from currency_quote.domain.entities.currency import CurrencyQuote, QuoteList


def make_quote(pair="USD-BRL", bid=5.0, ask=5.1):
    return CurrencyQuote(
        currency_pair=pair,
        currency_pair_name="Dólar Americano/Real Brasileiro",
        base_currency_code=pair.split("-")[0],
        quote_currency_code=pair.split("-")[1],
        quote_timestamp=1614024000,
        bid_price=bid,
        ask_price=ask,
    )


def test_quote_extracted_at_is_evaluated_per_instance():
    """Regression: the default used to be frozen at import time."""
    first = make_quote()
    time.sleep(1.1)
    second = make_quote()
    assert second.quote_extracted_at > first.quote_extracted_at


def test_quote_supports_mapping_access_for_backwards_compatibility():
    quote = make_quote()
    assert quote["currency_pair"] == "USD-BRL"
    assert quote.get("bid_price") == 5.0
    assert quote.get("missing", "fallback") == "fallback"
    assert dict(quote)["ask_price"] == 5.1

    with pytest.raises(KeyError):
        _ = quote["nope"]


def test_quote_derived_properties():
    quote = make_quote(bid=5.0, ask=5.2)
    assert quote.spread == pytest.approx(0.2)
    assert quote.mid_price == pytest.approx(5.1)
    assert quote.quote_datetime.year == 2021


def test_quote_list_to_dict_and_json():
    quotes = QuoteList([make_quote(), make_quote("EUR-BRL", 6.0, 6.1)])

    as_dict = quotes.to_dict()
    assert isinstance(as_dict, list)
    assert as_dict[0]["currency_pair"] == "USD-BRL"

    parsed = json.loads(quotes.to_json())
    assert len(parsed) == 2
    assert parsed[1]["currency_pair"] == "EUR-BRL"


def test_quote_list_pairs_and_filter():
    quotes = QuoteList([make_quote(), make_quote("EUR-BRL", 6.0, 6.1), make_quote()])
    assert quotes.pairs == ["USD-BRL", "EUR-BRL"]

    filtered = quotes.filter_by_pair("usd/brl")
    assert len(filtered) == 2
    assert isinstance(filtered, QuoteList)


def test_quote_list_to_dataframe():
    pd = pytest.importorskip("pandas")
    quotes = QuoteList([make_quote(), make_quote("EUR-BRL", 6.0, 6.1)])

    df = quotes.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert list(df["currency_pair"]) == ["USD-BRL", "EUR-BRL"]
    assert "bid_price" in df.columns
