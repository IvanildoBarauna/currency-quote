"""Command line interface: python -m currency_quote or currency-quote."""

import argparse
import csv
import json
import sys

from currency_quote.client import CurrencyQuoteClient
from currency_quote.exceptions import CurrencyQuoteError


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Get current and historical currency quotes"
    )
    parser.add_argument("pairs", nargs="+", help="e.g. USD-BRL EUR-BRL")
    parser.add_argument("--date", help="A single past date (YYYY-MM-DD)")
    parser.add_argument("--start", help="First day in a historical range")
    parser.add_argument("--end", help="Last day in a historical range")
    parser.add_argument("--no-validate", action="store_true")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="JSON output (default)")
    output.add_argument("--csv", action="store_true", help="CSV output")
    args = parser.parse_args(argv)
    if (args.date and (args.start or args.end)) or bool(args.start) != bool(args.end):
        parser.error("use --date or both --start and --end")

    try:
        with CurrencyQuoteClient(args.pairs, validate=not args.no_validate) as client:
            if args.date:
                quotes = client.get_history_quote(args.date)
            elif args.start:
                quotes = client.get_history_range(args.start, args.end)
            else:
                quotes = client.get_last_quote()
        rows = quotes.to_dict()
    except CurrencyQuoteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.csv:
        writer = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
