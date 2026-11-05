# currency-quote

Lightweight Python client for current and historical currency quotes from [AwesomeAPI](https://docs.awesomeapi.com.br/api-de-moedas). No API key required. Python 3.9–3.13.

## Installation

```sh
pip install currency-quote
# Optional DataFrame export:
pip install 'currency-quote[pandas]'
```

Runtime dependencies: `requests` (and its HTTP dependencies) and `tzdata` (so provider-local dates also work in minimal containers); pandas, numpy and pytest are **not** required for ordinary use.

## Quick start

```python
from decimal import Decimal
from currency_quote import CurrencyQuoteClient

with CurrencyQuoteClient("USD-BRL") as client:
    latest = client.get_last_quote()[0]
    print(latest.currency_pair, latest.bid_price)  # Decimal, safe for calculations
    print(latest.bid_price * Decimal("100"))
    print(client.get_history_quote("2024-06-03").to_dict())
    history = client.get_history_range("2024-06-01", "2024-06-07")
    print(history.to_dict())
    # history.to_dataframe()  # requires the [pandas] extra
```

`CurrencyQuoteClient` accepts `"USD-BRL"` or a list of pairs; surrounding whitespace and case are normalized, and duplicates are removed. Results are `list`-like `QuoteList[CurrencyQuote]`; `bid_price`, `ask_price` and optional high/low/change values are `Decimal`. `to_dict()` returns JSON-ready decimal strings and the original eight-field schema. Supported dates: `YYYYMMDD` integers or strings, `YYYY-MM-DD`, `DD/MM/YYYY` and Python `date`/`datetime`. A historical date must precede **today in America/Sao_Paulo**. Historical ranges include both endpoints and return newest-first records grouped by requested pair; days without provider records are omitted (some weekend dates do have records).

`quote_timestamp` and `quote_extracted_at` are Unix **seconds**. The adapter also
accepts provider history records with millisecond timestamps and normalizes
them to seconds before date filtering, ordering and serialization.

Both methods validate pairs against the provider by default. A per-client one-hour cache avoids fetching the available-pairs list for every call. Use `validate=False` to skip this lookup when your pairs are known; `timeout`, `retries` (extra attempts beyond the first) and `cache_ttl` can be set when constructing the client. A pooled HTTP connection is shared between validation and quotes. `repository=` and `validator=` accept implementations of the outbound ports for testing or alternate providers. Caller-injected HTTP sessions are not closed by the client.

**Failure behavior is strict:** if any pair is invalid, missing from a current response, or has no data in the requested historical day/range, the whole call raises an exception rather than silently returning a partial result. A range with data in some windows and no data in others succeeds with available records. `CurrencyQuoteError` catches all expected library failures; subclasses `InvalidCurrencyError`, `InvalidCurrencyTypeError`, `InvalidDateError`, `InvalidConfigError`, `NoDataForDateError` and `CurrencyAPIError` allow targeted handling. Provider outages, timeouts and malformed JSON produce `CurrencyAPIError`.

## Legacy client and migration to 6.0

```python
from currency_quote import ClientBuilder

with ClientBuilder("USD-BRL") as client:
    print(client.get_last_quote())           # list[dict]
    print(client.get_history_quote(20240603))  # list[dict]
```

The `ClientBuilder` constructor and methods still return lists of dictionaries with the **same eight keys**. In v5, current prices were strings but historical prices were floats; in v6 **both are decimal strings**. Use `Decimal(quote["bid_price"])` for arithmetic. Also new in v6: invalid dates and pairs, or missing historical data, raise typed exceptions instead of returning empty/partial lists or leaking `IndexError`. These are intentional breaking changes; migrate callers that depend on floats, silent filtering or empty results. New code should use `CurrencyQuoteClient` for typed `Decimal` results. Extended statistics are available as typed attributes on `CurrencyQuote`, without changing the legacy dict schema.

## CLI

```sh
currency-quote USD-BRL EUR-BRL
currency-quote USD-BRL --date 2024-06-03 --csv
currency-quote USD-BRL --start 2024-06-01 --end 2024-06-07
python -m currency_quote USD-BRL --no-validate
```

JSON is the default format; `--csv` emits CSV. Errors print to stderr with exit code 1. The CLI requires an internet connection.

## Development

```sh
poetry install
poetry run pytest -q
poetry run black --check src/currency_quote src/tests
poetry build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [LICENSE](LICENSE).

For maintainers and coding agents, see [AGENTS.md](AGENTS.md) and the
[changelog](CHANGELOG.md). Security reports should follow
[SECURITY.md](SECURITY.md).

## Release workflow

`pyproject.toml` proposes version **6.0.0** (latest published version: 5.0.7).
A merged PR targeting `main` must have the `deployable` label to start the
publishing job. GitHub's `Production` environment then **requires manual
approval** before a v6.0.0 GitHub release and PyPI upload; merge alone does not
complete publication. The `PYPI_TOKEN` secret must be configured. Automatic
Claude Code Review on PR opening was removed; `@claude` is still opt-in in
comments/reviews/issues.
