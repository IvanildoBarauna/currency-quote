# currency-quote

> Complete solution for extracting currency pair quotes data.

[![PyPI - Status](https://img.shields.io/pypi/status/currency-quote?style=for-the-badge&logo=pypi)](https://pypi.org/project/currency-quote/)
[![PyPI - Version](https://img.shields.io/pypi/v/currency-quote?style=for-the-badge&logo=pypi)](https://pypi.org/project/currency-quote/#history)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/currency-quote?style=for-the-badge&logo=pypi)](https://pypi.org/project/currency-quote/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/currency-quote?style=for-the-badge&logo=python)

[![CI](https://img.shields.io/github/actions/workflow/status/ivdatahub/currency-quote/CI.yaml?&style=for-the-badge&logo=githubactions&cacheSeconds=60&label=Tests+and+pre+build)](https://github.com/ivdatahub/currency-quote/actions/workflows/CI.yaml)
[![CD](https://img.shields.io/github/actions/workflow/status/ivdatahub/currency-quote/CD.yaml?&style=for-the-badge&logo=githubactions&cacheSeconds=60&event=release&label=Package+publication)](https://github.com/ivdatahub/currency-quote/actions/workflows/CD.yaml)
[![Codecov](https://img.shields.io/codecov/c/github/ivdatahub/currency-quote?style=for-the-badge&logo=codecov)](https://app.codecov.io/gh/ivdatahub/currency-quote)

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

```python
from currency_quote import ClientBuilder

# Single currency pair
client = ClientBuilder(currency_list="USD-BRL")

# Multiple currency pairs
client = ClientBuilder(currency_list=["USD-BRL", "EUR-BRL"])

# Get the latest quote
print(client.get_last_quote())

# Get historical quote for a specific date (YYYYMMDD)
print(client.get_history_quote(reference_date=20220101))
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
    "bid_price": 5.524,
    "ask_price": 5.5245,
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
| **Parameter Validation** | Currency pairs are validated against the data source before any request |
| **Retry Strategy** | Configurable retry logic with exponential and linear backoff |
| **Hexagonal Architecture** | Core logic fully decoupled from external APIs |
| **CI/CD** | Automated testing, build, and PyPI publication pipelines |
| **Code Quality** | Black formatting + Pylint enforced on every commit |

---

## Contributing

- [Contributing Guide](https://github.com/ivdatahub/currency-quote/blob/main/CONTRIBUTING.md)
- [Code of Conduct](https://github.com/ivdatahub/currency-quote/blob/main/CODE_OF_CONDUCT.md)
