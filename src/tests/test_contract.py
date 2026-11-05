"""Exercise the public API using injected provider and parity fakes."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from currency_quote import (
    ClientBuilder,
    CurrencyQuote,
    CurrencyQuoteClient,
    CurrencyQuoteError,
    InvalidCurrencyError,
    InvalidCurrencyTypeError,
    InvalidDateError,
    NoDataForDateError,
)
from currency_quote.domain.entities.currency import CurrencyObject
from currency_quote.client import QuoteList


def quote(pair="USD-BRL", timestamp=1717426800):
    return CurrencyQuote(
        pair,
        "Dólar/Real",
        "USD",
        "BRL",
        timestamp,
        Decimal("5.0876"),
        Decimal("5.0891"),
    )


@pytest.mark.parametrize(
    "pairs,expected",
    [
        (" usd-brl ", ["USD-BRL"]),
        (["USD-BRL", "usd-brl", "EUR-BRL"], ["USD-BRL", "EUR-BRL"]),
        (["USD-BRLT"], ["USD-BRLT"]),
    ],
)
def test_pair_normalization(pairs, expected):
    assert CurrencyObject(pairs).get_currency_list() == expected


@pytest.mark.parametrize(
    "value", [[], ["INVALID"], ["USD-BR"], ["USD-123"], ["ÚSD-BRL"]]
)
def test_pair_format_is_typed(value):
    with pytest.raises(InvalidCurrencyError):
        CurrencyObject(value)


@pytest.mark.parametrize("value", [1, [1], ["USD-BRL", None]])
def test_pair_type_is_typed(value):
    with pytest.raises(InvalidCurrencyTypeError):
        CurrencyObject(value)


def test_client_returns_exact_decimal_and_legacy_dict_schema():
    repository = Mock()
    repository.get_last_quote.return_value = [quote()]
    client = CurrencyQuoteClient("usd-brl", repository=repository, validate=False)
    result = client.get_last_quote()
    assert result[0].bid_price + Decimal("0.0001") == Decimal("5.0877")
    assert result.to_dict()[0]["bid_price"] == "5.0876"
    assert len(result.to_dict()[0]) == 8
    repository.get_last_quote.assert_called_once_with(["USD-BRL"])
    with ClientBuilder("USD-BRL", repository=repository, validate=False) as legacy:
        assert legacy.get_last_quote() == result.to_dict()
    client.close()


def test_history_date_validated_before_any_provider_call():
    repository, validator = Mock(), Mock()
    client = CurrencyQuoteClient("USD-BRL", repository=repository, validator=validator)
    for value in (20220230, 20221301, 2022011, True, "tomorrow", date(2999, 1, 1)):
        with pytest.raises(InvalidDateError):
            client.get_history_quote(value)
    with pytest.raises(InvalidDateError):
        client.get_history_range("2024-06-05", "2024-06-01")
    repository.get_history.assert_not_called()
    validator.available_pairs.assert_not_called()
    client.close()


def test_validation_rejects_mixed_pairs_without_fetching_quotes():
    repo, validator = Mock(), Mock()
    validator.available_pairs.return_value = {"USD-BRL"}
    client = CurrencyQuoteClient(
        ["USD-BRL", "AAA-BBB"], repository=repo, validator=validator
    )
    with pytest.raises(InvalidCurrencyError, match="AAA-BBB") as exc:
        client.get_last_quote()
    assert isinstance(exc.value, CurrencyQuoteError)
    repo.get_last_quote.assert_not_called()
    client.close()


def test_history_is_ordered_per_pair_and_fails_if_one_pair_has_no_data():
    repo = Mock()
    repo.get_history.side_effect = [[quote(timestamp=2), quote(timestamp=3)], []]
    client = CurrencyQuoteClient(
        ["USD-BRL", "EUR-BRL"], repository=repo, validate=False
    )
    with pytest.raises(NoDataForDateError, match="EUR-BRL"):
        client.get_history_range("2024-06-01", "2024-06-05")
    repo.get_history.side_effect = None
    repo.get_history.return_value = [quote(timestamp=2), quote(timestamp=3)]
    assert [q.quote_timestamp for q in client.get_history_quote(20240603)] == [
        3,
        2,
        3,
        2,
    ]
    client.close()


def test_timestamp_default_is_evaluated_for_each_quote(monkeypatch):
    from currency_quote.domain.entities import currency

    values = iter([100, 110])
    monkeypatch.setattr(currency, "time", lambda: next(values))
    assert quote().quote_extracted_at == 100
    assert quote().quote_extracted_at == 110


def test_history_accepts_brazilian_dates_and_date_instances():
    repo = Mock()
    repo.get_history.return_value = [quote()]
    with CurrencyQuoteClient("USD-BRL", repository=repo, validate=False) as client:
        assert len(client.get_history_quote("03/06/2024")) == 1
        repo.get_history.assert_called_with(
            "USD-BRL", date(2024, 6, 3), date(2024, 6, 3)
        )
        assert len(client.get_history_range(date(2024, 6, 3), "2024-06-07")) == 1


def test_dataframes_are_only_imported_when_requested(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def no_pandas(name, *args, **kwargs):
        if name == "pandas":
            raise ImportError("not installed")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_pandas)
    with pytest.raises(ImportError, match="currency-quote\\[pandas\\]"):
        QuoteList([quote()]).to_dataframe()
