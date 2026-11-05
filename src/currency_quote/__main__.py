# src/currency_quote/__main.py
"""Command line interface: inspect quotes without writing any code."""
import argparse
import json
import sys
from typing import List, Optional, Sequence

from currency_quote import __version__
from currency_quote.client import CurrencyQuoteClient
from currency_quote.exceptions import CurrencyQuoteError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="currency-quote",
        description="Fetch currency pair quotes from the AwesomeAPI (economia).",
    )
    parser.add_argument(
        "currencies",
        nargs="+",
        help="Currency pair(s), e.g. USD-BRL EUR-BRL",
    )
    parser.add_argument(
        "--history",
        dest="history",
        default=None,
        help="Historical quote for a day (YYYY-MM-DD, DD/MM/YYYY or YYYYMMDD)",
    )
    parser.add_argument(
        "--start",
        dest="start",
        default=None,
        help="History range start date (use with --end)",
    )
    parser.add_argument(
        "--end",
        dest="end",
        default=None,
        help="History range end date (use with --start)",
    )
    parser.add_argument(
        "--no-validate",
        dest="no_validate",
        action="store_true",
        help="Skip the pre-validation round-trip against the parities endpoint",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    client = CurrencyQuoteClient(validate=not args.no_validate)

    try:
        quotes = run_query(client, args)
    except CurrencyQuoteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps([quote.to_dict() for quote in quotes], indent=2, ensure_ascii=False)
    )
    return 0


def run_query(client: CurrencyQuoteClient, args: argparse.Namespace) -> List:
    currencies = args.currencies
    if args.history is not None:
        return client.get_history(currencies, reference_date=args.history)
    if args.start is not None or args.end is not None:
        return client.get_history(currencies, start_date=args.start, end_date=args.end)
    return client.get_last(currencies)


if __name__ == "__main__":
    sys.exit(main())
