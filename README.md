# currency-quote

> Get current and historical currency pair quotes from [AwesomeAPI](https://docs.awesomeapi.com.br/api-de-moedas).

[![PyPI - Status](https://img.shields.io/pypi/status/currency-quote?style=for-the-badge&logo=pypi)](https://pypi.org/project/currency-quote/)
[![PyPI - Version](https://img.shields.io/pypi/v/currency-quote?style=for-the-badge&logo=pypi)](https://pypi.org/project/currency-quote/#history)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/currency-quote?style=for-the-badge&logo=pypi)](https://pypi.org/project/currency-quote/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/currency-quote?style=for-the-badge&logo=python)

[![CI](https://img.shields.io/github/actions/workflow/status/IvanildoBarauna/currency-quote/CI.yaml?style=for-the-badge&logo=githubactions&label=Tests)](https://github.com/IvanildoBarauna/currency-quote/actions/workflows/CI.yaml)
[![Codecov](https://img.shields.io/codecov/c/github/IvanildoBarauna/currency-quote?style=for-the-badge&logo=codecov)](https://app.codecov.io/gh/IvanildoBarauna/currency-quote)

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ivanildobarauna-dev/currency-quote)

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

Install with Python 3.9 or newer:

```sh
pip install currency-quote
```

```python
from currency_quote import ClientBuilder

# Single currency pair
client = ClientBuilder(currency_list="USD-BRL")

# Multiple currency pairs
client = ClientBuilder(currency_list=["USD-BRL", "EUR-BRL"])

# Get the latest quote
print(client.get_last_quote())

# Get historical quote for a specific date (YYYYMMDD)
print(client.get_history_quote(reference_date=20240626))
```

Both methods return a list of dictionaries, one per requested pair. Prices are
decimal **strings** (use `Decimal(quote["bid_price"])` for calculations without
floating-point rounding). `quote_timestamp` and `quote_extracted_at` are Unix
timestamps in seconds; the latter records when each result was constructed.
The historical method accepts an integer `YYYYMMDD` strictly before today.

Pairs must be listed by the [AwesomeAPI available pairs endpoint](https://economia.awesomeapi.com.br/json/available).
Invalid pairs or dates raise `ValueError` rather than returning partial data.
If a valid pair has no quote for the requested date, the historical method
raises `LookupError`. Network/provider errors propagate from the HTTP client;
this package requires an internet connection and depends on AwesomeAPI availability.

### Migration notes for the next major release

Compared with 5.x, historical prices are now decimal strings instead of
floats, matching the latest-quote response. Convert with `Decimal(price)`
when doing arithmetic. Mixed valid/invalid pair lists now raise `ValueError`
instead of silently omitting pairs; invalid historical dates also raise
`ValueError` instead of returning an empty list. Missing historical quotes
raise `LookupError`. Catch these exceptions if your application previously
treated empty or partial results as successful requests.

### Last quote response

```json
[
  {
    "currency_pair": "USD-BRL",
    "currency_pair_name": "Dólar Americano/Real Brasileiro",
    "base_currency_code": "USD",
    "quote_currency_code": "BRL",
    "quote_timestamp": 1727201744,
    "bid_price": "5.4579",
    "ask_price": "5.4589",
    "quote_extracted_at": 1727201753
  }
]
```

### Historical quote response

```json
[
  {
    "currency_pair": "USD-BRL",
    "currency_pair_name": "Dólar Americano/Real Brasileiro",
    "base_currency_code": "USD",
    "quote_currency_code": "BRL",
    "quote_timestamp": 1719440767,
    "bid_price": "5.524",
    "ask_price": "5.5245",
    "quote_extracted_at": 1727201753
  }
]
```

---

## Architecture

This library follows **Hexagonal Architecture** (ports & adapters), decoupling core business logic from external data sources so any API can be swapped without touching domain code.

![Hexagonal Design](./hexagonal_design_arch.png)

---

## Highlights

| Feature | Description |
|---|---|
| **Parameter Validation** | Currency pairs are checked against the data source before quote requests |
| **Retry Strategy** | Exponential retries for quotes and linear retries for pair validation |
| **Hexagonal Architecture** | Core logic fully decoupled from external APIs |
| **CI/CD** | Automated testing, build, and PyPI publication pipelines |
| **Code Quality** | Black formatting + Pylint enforced on every commit |

---

## Contributing

- [Contributing Guide](https://github.com/IvanildoBarauna/currency-quote/blob/main/CONTRIBUTING.md)
- [Code of Conduct](https://github.com/IvanildoBarauna/currency-quote/blob/main/CODE_OF_CONDUCT.md)
