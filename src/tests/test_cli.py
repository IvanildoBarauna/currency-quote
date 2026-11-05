"""CLI success and typed failure, without relying on internet availability."""

from decimal import Decimal
from unittest.mock import patch

from currency_quote.__main__ import main
from currency_quote.client import QuoteList
from currency_quote.domain.entities.currency import CurrencyQuote
from currency_quote.exceptions import InvalidCurrencyError


def test_cli_json_and_csv(capsys):
    quote = CurrencyQuote(
        "USD-BRL", "Dólar/Real", "USD", "BRL", 123, Decimal("5.10"), Decimal("5.11")
    )
    with patch("currency_quote.__main__.CurrencyQuoteClient") as factory:
        factory.return_value.__enter__.return_value.get_last_quote.return_value = (
            QuoteList([quote])
        )
        assert main(["USD-BRL"]) == 0
        assert '"bid_price": "5.10"' in capsys.readouterr().out
        assert main(["USD-BRL", "--csv"]) == 0
        assert "USD-BRL" in capsys.readouterr().out


def test_cli_error_is_not_a_traceback(capsys):
    with patch(
        "currency_quote.__main__.CurrencyQuoteClient",
        side_effect=InvalidCurrencyError("bad pair"),
    ):
        assert main(["AAA-BBB"]) == 1
    assert "error: bad pair" in capsys.readouterr().err
