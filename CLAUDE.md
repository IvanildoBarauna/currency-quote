# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run tests: `poetry run pytest`
- Run specific test: `poetry run pytest src/tests/test_file.py::test_function`
- Coverage: `poetry run coverage run -m pytest` && `poetry run coverage report`
- Format code: `poetry run black .`
- Lint: `poetry run pylint src`
- Build: `poetry build`
- Install: `poetry install`

## Architecture

This is a Python library (`currency-quote`) published to PyPI. It exposes a single public class `ClientBuilder` (from `currency_quote/__init__.py`) that users import to fetch currency pair quotes.

The project follows **Hexagonal Architecture** with three concentric layers:

### 1. Domain (`domain/`)
- `entities/currency.py` — `CurrencyObject` (validated input) and `CurrencyQuote` (dataclass output)
- `services/get_currency_quote.py` — `GetCurrencyQuoteService`: orchestrates validation + quote fetching, injects `ICurrencyRepository`
- `services/validate_currency.py` — `CurrencyValidatorService`: filters valid currency pairs via injected `ICurrencyValidator`

### 2. Application (`application/`)
- **Ports (interfaces):**
  - `ports/inbound/controller.py` — `IController` (abstract base for entry points)
  - `ports/outbound/currency_repository.py` — `ICurrencyRepository` (get_last_quote / get_history_quote)
  - `ports/outbound/currency_validator_repository.py` — `ICurrencyValidator`
- **Use cases** wire domain services to concrete adapters: `GetLastCurrencyQuoteUseCase`, `GetHistCurrencyQuoteUseCase`, `ValidateCurrencyUseCase`

### 3. Adapters (`adapters/`)
- **Inbound:** `lib_controller.py` → `ClientBuilder` implements `IController`, translates `CurrencyQuote` dataclasses into plain dicts for the caller
- **Outbound:**
  - `currency_api.py` → `CurrencyAPI` implements `ICurrencyRepository`, calls `https://economia.awesomeapi.com.br`
  - `currency_validator_api.py` → `CurrencyValidatorAPI` implements `ICurrencyValidator`, validates pairs against the available parities endpoint

### Request flow
```
ClientBuilder.get_last_quote()
  → GetLastCurrencyQuoteUseCase.execute()
    → GetCurrencyQuoteService.last()
      → ValidateCurrencyUseCase (filters invalid pairs via CurrencyValidatorAPI)
      → CurrencyAPI.get_last_quote() (fetches from awesomeapi)
    → returns List[CurrencyQuote]
  → serialized to List[dict]
```

### External dependency
`api-to-dataframe` (`ClientBuilder`, `RetryStrategies`) handles HTTP requests with retry logic. All outbound HTTP calls go through this library.

## Code Style
- Python 3.9+ with type hints required on all function signatures
- Black formatting, PEP 8
- `snake_case` functions, `PascalCase` classes
- Pylint rules: `C0114` (module docstring), `C0116` (function docstring), and `R0903` (too-few-public-methods) are disabled
- Tests use `unittest.mock` with fixtures defined in `src/tests/conftest.py`; currency API calls are always mocked in tests
