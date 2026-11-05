"""Command line interface for currency-quote."""

import argparse
import logging
import sys
from typing import List, Optional, Sequence

from currency_quote.adapters.inbound.lib_controller import CurrencyQuoteClient
from currency_quote.config.settings import RequestConfig, RetryStrategy
from currency_quote.domain.entities.currency import QuoteList
from currency_quote.exceptions import CurrencyQuoteError
from currency_quote.utils.logger import setup_logging

_COLUMNS = [
    ("currency_pair", "PAIR"),
    ("quote_datetime", "DATE"),
    ("bid_price", "BID"),
    ("ask_price", "ASK"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="currency-quote",
        description="Fetch currency pair quotes from the command line.",
        epilog=(
            "Examples:\n"
            "  currency-quote USD-BRL\n"
            "  currency-quote USD-BRL EUR-BRL --json\n"
            "  currency-quote USD-BRL --date 2024-06-26\n"
            "  currency-quote USD-BRL --start 2024-06-01 --end 2024-06-30 --csv\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "pairs",
        nargs="+",
        metavar="PAIR",
        help="Currency pairs, e.g. USD-BRL EUR-BRL",
    )
    parser.add_argument("--date", help="Single past date (YYYY-MM-DD or YYYYMMDD)")
    parser.add_argument("--start", help="Start of a historical date range")
    parser.add_argument("--end", help="End of a historical date range")

    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Output JSON")
    output.add_argument("--csv", action="store_true", help="Output CSV")

    parser.add_argument(
        "--timeout", type=int, default=10, help="Connection timeout in seconds"
    )
    parser.add_argument(
        "--retries", type=int, default=3, help="Number of retry attempts"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip the currency pair validation request",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.verbose:
        setup_logging(logging.DEBUG)

    if args.date and (args.start or args.end):
        print("error: use either --date or --start/--end, not both", file=sys.stderr)
        return 2
    if args.end and not args.start:
        print("error: --end requires --start", file=sys.stderr)
        return 2

    try:
        config = RequestConfig(
            retry_strategy=RetryStrategy.EXPONENTIAL,
            retries=args.retries,
            timeout=args.timeout,
        )
        client = CurrencyQuoteClient(
            args.pairs, config=config, validate=not args.no_validate
        )
        if args.date:
            quotes = client.get_history_quote(args.date)
        elif args.start:
            quotes = client.get_history_range(args.start, args.end)
        else:
            quotes = client.get_last_quote()
    except (CurrencyQuoteError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(quotes.to_json(indent=2))
    elif args.csv:
        print(_render_csv(quotes))
    else:
        print(_render_table(quotes))

    return 0


def _rows(quotes: QuoteList) -> List[List[str]]:
    rows = []
    for quote in quotes:
        row = []
        for key, _ in _COLUMNS:
            if key == "quote_datetime":
                row.append(quote.quote_datetime.strftime("%Y-%m-%d %H:%M"))
            else:
                row.append(str(quote[key]))
        rows.append(row)
    return rows


def _render_table(quotes: QuoteList) -> str:
    headers = [label for _, label in _COLUMNS]
    rows = _rows(quotes)
    widths = [
        (
            max(len(headers[i]), *(len(row[i]) for row in rows))
            if rows
            else len(headers[i])
        )
        for i in range(len(headers))
    ]

    def line(values: List[str]) -> str:
        return "  ".join(value.ljust(widths[i]) for i, value in enumerate(values))

    output = [line(headers), "  ".join("-" * width for width in widths)]
    output.extend(line(row) for row in rows)
    return "\n".join(output)


def _render_csv(quotes: QuoteList) -> str:
    import csv  # pylint: disable=import-outside-toplevel
    import io  # pylint: disable=import-outside-toplevel

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([label for _, label in _COLUMNS])
    writer.writerows(_rows(quotes))
    return buffer.getvalue().strip()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
