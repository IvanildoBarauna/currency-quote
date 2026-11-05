# currency-quote

> Complete solution for extracting currency pair quotes data.

[![PyPI - Status](https://img.shields.io/pypi/status/currency-quote?style=for-the-badge&logo=pypi)](https://pypi.org/project/currency-quote/)
[![PyPI - Version](https://img.shields.io/pypi/v/currency-quote?style=for-the-badge&logo=pypi)](https://pypi.org/project/currency-quote/#history)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/currency-quote?style=for-the-badge&logo=pypi)](https://pypi.org/project/currency-quote/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/currency-quote?style=for-the-badge&logo=python)

[![CI](https://img.shields.io/github/actions/workflow/status/IvanildoBarauna/currency-quote/CI.yaml?&style=for-the-badge&logo=githubactions&cacheSeconds=60&label=Tests+and+pre+build)](https://github.com/IvanildoBarauna/currency-quote/actions/workflows/CI.yaml)
[![CD](https://img.shields.io/github/actions/workflow/status/IvanildoBarauna/currency-quote/CD.yaml?&style=for-the-badge&logo=githubactions&cacheSeconds=60&event=release&label=Package+publication)](https://github.com/IvanildoBarauna/currency-quote/actions/workflows/CD.yaml)
[![Codecov](https://img.shields.io/codecov/c/github/IvanildoBarauna/currency-quote?style=for-the-badge&logo=codecov)](https://app.codecov.io/gh/IvanildoBarauna/currency-quote)

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/IvanildoBarauna/currency-quote)

---

## Stack

![Python](https://img.shields.io/badge/-Python-05122A?style=flat&logo=python)&nbsp;
![Poetry](https://img.shields.io/badge/-Poetry-05122A?style=flat&logo=poetry)&nbsp;
![pytest](https://img.shields.io/badge/-pytest-05122A?style=flat&logo=pytest)&nbsp;
![GitHub Actions](https://img.shields.io/badge/-GitHub_Actions-05122A?style=flat&logo=githubactions)&nbsp;
![CodeCov](https://img.shields.io/badge/-CodeCov-05122A?style=flat&logo=codecov)&nbsp;
![pypi](https://img.shields.io/badge/-pypi-05122A?style=flat&logo=pypi)&nbsp;

---

## Quick Start

```python
from currency_quote import CurrencyQuoteClient

client = CurrencyQuoteClient()

# Latest quotes for several pairs at once
quotes = client.get_last("USD-BRL", "EUR-BRL")

for quote in quotes:
    print(quote.currency_pair, quote.bid_price, quote.high_price, quote.pct_change)

# One-row DataFrame (requires `pip install 'currency-quote[pandas]'`)
frame = quotes.to_dataframe()
print(frame[["currency_pair", "bid_price", "pct_change"]])

# Historical quote for a single past day (YYYYMMDD, 'YYYY-MM-DD', 'DD/MM/YYYY' or a date)
client.get_history("USD-BRL", reference_date="2024-01-05")

# Historical range (chronological order, per pair)
client.get_history("USD-BRL", start_date="2024-01-02", end_date="2024-01-05")
```

### Last quote response

```json
[
  {
    "currency_pair": "USD-BRL",
    "currency_pair_name": "Dólar Americano/Real Brasileiro",
    "base_currency_code": "USD",
    "quote_currency_code": "BRL",
    "quote_timestamp": 1727201744,
    "bid_price": 5.4579,
    "ask_price": 5.4589,
    "quote_extracted_at": 1727201753,
    "high_price": 5.4945,
    "low_price": 5.4274,
    "var_bid": 0.0276,
    "pct_change": 0.5055
  }
]
```

### Backward compatible client (v5 style)

`ClientBuilder` is still available and keeps returning plain dicts:

```python
from currency_quote import ClientBuilder

client = ClientBuilder(currency_list=["USD-BRL", "EUR-BRL"])
print(client.get_last_quote())          # List[dict]
print(client.get_history_quote(reference_date=20240105))  # List[dict]
```

---

## CLI

After `pip install currency-quote` you get a terminal helper:

```bash
currency-quote USD-BRL EUR-BRL
currency-quote USD-BRL --history 2024-01-05
currency-quote USD-BRL --start 2024-01-02 --end 2024-01-05
currency-quote USD-BRL --no-validate
```

Output is JSON (one object per quote), ready to be piped into `jq` or any script.

---

## Error handling

The library raises typed exceptions (all inherit from `currency_quote.CurrencyQuoteError`):

| Exception | When |
|---|---|
| `InvalidCurrencyPairError` | input has the wrong type |
| `CurrencyPairValidationError` | malformed pair or rejected by the parities endpoint |
| `InvalidDateError` | date is malformed, in the future or inverted |
| `NoDataForDateError` | market closed (weekend/holiday) or pair has no daily archive |
| `CurrencyAPIError` | network / gateway failure |

```python
from currency_quote import CurrencyQuoteClient, NoDataForDateError

client = CurrencyQuoteClient()
try:
    client.get_history("USD-BRL", reference_date=20240619)
except NoDataForDateError:
    print("No trading data for that date (weekend/holiday).")
```

---

## Architecture

This library follows **Hexagonal Architecture** (ports & adapters), decoupling core business logic from external data sources so any API can be swapped without touching domain code.

![Hexagonal Design](./hexagonal_design_arch.png)

---

## Highlights

| Feature | Description |
|---|---|
| **Parameter Validation** | Currency pairs are validated against the data source before any request |
| **Retry Strategy** | Configurable retry logic with exponential backoff |
| **Flexible Dates** | `int`, `'YYYY-MM-DD'`, `'DD/MM/YYYY'`, `date`, `datetime` all accepted |
| **History Ranges** | Chronological quotes over a date range (paginated by year) |
| **Typed Results** | `CurrencyQuote` dataclasses with `to_dict()` / `to_dataframe()` |
| **Extra Statistics** | `high`, `low`, `var_bid`, `pct_change` available on every quote |
| **Parity Cache** | The parities list is cached (TTL 1h) to save an HTTP request per call |
| **Optional Pandas** | `pip install 'currency-quote[pandas]'` enables DataFrame exports |
| **CLI** | `currency-quote USD-BRL` from the terminal |
| **Lightweight** | Only `requests` as a runtime dependency (no pandas unless you want it) |
| **Hexagonal Architecture** | Core logic fully decoupled from external APIs |
| **CI/CD** | Automated testing (Python 3.9–3.13), build, and PyPI publication pipelines |
| **Code Quality** | Black formatting + Pylint enforced on every commit |

---

## Contributing

- [Contributing Guide](https://github.com/IvanildoBarauna/currency-quote/blob/main/CONTRIBUTING.md)
- [Code of Conduct](https://github.com/IvanildoBarauna/currency-quote/blob/main/CODE_OF_CONDUCT.md)

---

## Guia rápido em português 🇧🇷

```python
from currency_quote import CurrencyQuoteClient

client = CurrencyQuoteClient()

# Cotação atual (vários pares de uma vez)
cotacoes = client.get_last("USD-BRL", "EUR-BRL")
for c in cotacoes:
    print(c.currency_pair, c.bid_price, c.pct_change)

# Histórico de um dia específico
client.get_history("USD-BRL", reference_date="2024-01-05")

# Histórico de um intervalo (ordenado cronologicamente)
client.get_history("USD-BRL", start_date="2024-01-02", end_date="2024-01-05")

# Exportar para DataFrame (requer pip install 'currency-quote[pandas]')
cotacoes.to_dataframe()
```

Na linha de comando:

```bash
currency-quote USD-BRL EUR-BRL
currency-quote USD-BRL --history 2024-01-05
```
