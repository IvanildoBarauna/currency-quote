# currency-quote

**Real-time and historical currency exchange rates for Python.** Fetch currency pairs from [AwesomeAPI](https://docs.awesomeapi.com.br/api-de-moedas), with typed results, retries, validation, date ranges, a CLI, and optional pandas integration. No API key required.

[![PyPI version](https://img.shields.io/pypi/v/currency-quote)](https://pypi.org/project/currency-quote/)
[![Python versions](https://img.shields.io/pypi/pyversions/currency-quote)](https://pypi.org/project/currency-quote/)
[![Downloads](https://img.shields.io/pypi/dm/currency-quote)](https://pypi.org/project/currency-quote/)
[![Tests](https://github.com/IvanildoBarauna/currency-quote/actions/workflows/CI.yaml/badge.svg)](https://github.com/IvanildoBarauna/currency-quote/actions/workflows/CI.yaml)

## Installation

Requires Python 3.9 or newer.

```bash
pip install currency-quote
# or, for DataFrame support:
pip install "currency-quote[pandas]"
```

## Quick start

```python
from currency_quote import CurrencyQuoteClient

client = CurrencyQuoteClient(["USD-BRL", "EUR-BRL"])

# Current quotes (one request for all pairs)
quotes = client.get_last_quote()
for quote in quotes:
    print(quote.currency_pair, quote.bid_price, quote.ask_price)
    print("Spread:", quote.spread, "Midpoint:", quote.mid_price)

# Historical close on one day (date, datetime, YYYYMMDD int or string)
history = client.get_history_quote("2024-06-26")

# Inclusive date range (daily closes; weekends/holidays may have no data)
series = client.get_history_range("2024-06-01", "2024-06-30")
print(series.to_dict())       # list[dict]
print(series.to_json())       # JSON string
print(series.to_dataframe())  # requires currency-quote[pandas]
```

Pairs are normalized: `"usd/brl"`, `"USD_BRL"`, and `"USD-BRL"` all resolve to `USD-BRL`. Invalid pairs are filtered out by default; if *all* pairs are unavailable, a `CurrencyNotFoundError` is raised. Use `client.currencies` to inspect normalized inputs.

Results are `QuoteList` objects, a subclass of `list[CurrencyQuote]`. `CurrencyQuote` supports both attribute access (`quote.bid_price`) and mapping-style access (`quote["bid_price"]`); prices are `float`, timestamps are Unix seconds. `quote.quote_datetime` is a local, timezone-naive `datetime`. Historical data is returned in provider order (newest first per pair). Use `.filter_by_pair("USD-BRL")` or `.pairs` when working with multiple currencies.

> **Upgrading from v5:** `ClientBuilder` remains an alias of `CurrencyQuoteClient`, but `get_last_quote()` and `get_history_quote()` now return typed quotes rather than plain dictionaries; use `.to_dict()` to recover `list[dict]`. Bid/ask prices are consistently floats. Invalid dates now raise `InvalidDateError` instead of silently returning `[]`. If you rely on exact return types, treat this as a breaking change.

## Command line

```bash
currency-quote USD-BRL
currency-quote USD-BRL EUR-BRL --json
currency-quote USD-BRL --date 2024-06-26 --csv
currency-quote USD-BRL --start 2024-06-01 --end 2024-06-30 --csv
currency-quote USD-BRL --timeout 30 --retries 5 --no-validate
```

The CLI exits with status 0 on success, 1 on a lookup error, and 2 on incompatible flags. Run `currency-quote --help` for all options.

## Configuration and error handling

```python
from currency_quote import (
    CurrencyQuoteClient, RequestConfig, RetryStrategy,
    CurrencyQuoteError, InvalidDateError, QuoteFetchError,
)

client = CurrencyQuoteClient(
    "USD-BRL",
    config=RequestConfig(
        retry_strategy=RetryStrategy.EXPONENTIAL,
        retries=5,
        initial_delay=2,
        timeout=30,       # connection timeout, in seconds
        max_workers=4,    # parallel history requests
    ),
    validate=False,       # skip availability lookup if pairs are known
)

try:
    quotes = client.get_last_quote()
except InvalidDateError:
    ...  # malformed, current, or future date (for historical queries)
except QuoteFetchError:
    ...  # network or upstream response failure
except CurrencyQuoteError:
    ...  # any other error from this package
```

By default, the list of available currency pairs is cached in memory for one hour; call `clear_available_parities_cache()` from `currency_quote` to refresh it. The cache is process-local and is not shared across workers. HTTP requests use `api-to-dataframe` underneath. The data source may enforce rate limits and availability windows; currency-quote does not provide an SLA or a guaranteed historical archive.

### Async applications

```python
quotes = await client.get_last_quote_async()
history = await client.get_history_quote_async("2024-06-26")
series = await client.get_history_range_async("2024-06-01", "2024-06-30")
```

These methods offload the synchronous HTTP client to a worker thread (Python 3.9+). They do not provide native async HTTP or cancel an in-flight request when the task is cancelled.

### Alternative data sources

You can pass a repository class implementing `ICurrencyRepository` (from `currency_quote.application.ports.outbound.currency_repository`) via `repository=MyRepository`. Set `validate=False` when using a different provider: the default pair validator checks AwesomeAPI's list. The repository constructor accepts `(CurrencyObject, RequestConfig)` and implements `get_last_quote()`, `get_history_quote(reference_date)` and `get_history_quote_range(start_date, end_date)`, returning `QuoteList` objects.

## Development

```bash
poetry install
poetry run pytest
poetry run black --check src
poetry run pylint src/currency_quote
poetry build
```

Contributions are welcome: see [CONTRIBUTING.md](https://github.com/IvanildoBarauna/currency-quote/blob/main/CONTRIBUTING.md), [CHANGELOG.md](https://github.com/IvanildoBarauna/currency-quote/blob/main/CHANGELOG.md) and [SECURITY.md](https://github.com/IvanildoBarauna/currency-quote/blob/main/SECURITY.md). Licensed under [MIT](LICENSE).
