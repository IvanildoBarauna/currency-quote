import json
from unittest.mock import patch

import pytest

from currency_quote.adapters.inbound.cli import main
from currency_quote.domain.entities.currency import CurrencyQuote, QuoteList
from currency_quote.exceptions import CurrencyNotFoundError

CLIENT = "currency_quote.adapters.inbound.cli.CurrencyQuoteClient"


def sample_quotes():
    return QuoteList(
        [
            CurrencyQuote(
                currency_pair="USD-BRL",
                currency_pair_name="Dólar Americano/Real Brasileiro",
                base_currency_code="USD",
                quote_currency_code="BRL",
                quote_timestamp=1614024000,
                bid_price=5.0876,
                ask_price=5.0891,
            )
        ]
    )


def test_cli_prints_table(capsys):
    with patch(CLIENT) as client:
        client.return_value.get_last_quote.return_value = sample_quotes()
        assert main(["USD-BRL"]) == 0

    out = capsys.readouterr().out
    assert "PAIR" in out
    assert "USD-BRL" in out
    assert "5.0876" in out


def test_cli_json_output(capsys):
    with patch(CLIENT) as client:
        client.return_value.get_last_quote.return_value = sample_quotes()
        assert main(["USD-BRL", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["currency_pair"] == "USD-BRL"


def test_cli_csv_output(capsys):
    with patch(CLIENT) as client:
        client.return_value.get_last_quote.return_value = sample_quotes()
        assert main(["USD-BRL", "--csv"]) == 0

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[0] == "PAIR,DATE,BID,ASK"
    assert lines[1].startswith("USD-BRL,")


def test_cli_single_date_uses_history(capsys):
    with patch(CLIENT) as client:
        client.return_value.get_history_quote.return_value = sample_quotes()
        assert main(["USD-BRL", "--date", "2024-06-26"]) == 0
        client.return_value.get_history_quote.assert_called_once_with("2024-06-26")


def test_cli_range_uses_history_range():
    with patch(CLIENT) as client:
        client.return_value.get_history_range.return_value = sample_quotes()
        assert main(["USD-BRL", "--start", "2024-06-01", "--end", "2024-06-30"]) == 0
        client.return_value.get_history_range.assert_called_once_with(
            "2024-06-01", "2024-06-30"
        )


def test_cli_rejects_date_combined_with_range(capsys):
    assert main(["USD-BRL", "--date", "2024-06-26", "--start", "2024-06-01"]) == 2
    assert "not both" in capsys.readouterr().err


def test_cli_rejects_end_without_start(capsys):
    assert main(["USD-BRL", "--end", "2024-06-30"]) == 2
    assert "requires --start" in capsys.readouterr().err


def test_cli_reports_library_errors(capsys):
    with patch(CLIENT) as client:
        client.return_value.get_last_quote.side_effect = CurrencyNotFoundError(
            ["AAA-BBB"]
        )
        assert main(["AAA-BBB"]) == 1

    assert "error:" in capsys.readouterr().err


def test_cli_forwards_transport_options():
    with patch(CLIENT) as client:
        client.return_value.get_last_quote.return_value = sample_quotes()
        main(["USD-BRL", "--timeout", "30", "--retries", "5", "--no-validate"])

    kwargs = client.call_args.kwargs
    assert kwargs["config"].timeout == 30
    assert kwargs["config"].retries == 5
    assert kwargs["validate"] is False


def test_cli_reports_bad_transport_options(capsys):
    assert main(["USD-BRL", "--timeout", "0"]) == 1
    assert "timeout must be > 0" in capsys.readouterr().err
