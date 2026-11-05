# Contributing to currency-quote

Thanks for helping improve [`currency-quote`](https://github.com/IvanildoBarauna/currency-quote).
See [README.md](README.md) for the API contract and migration guide, and
[AGENTS.md](AGENTS.md) for architecture and release safeguards.

## Getting started

1. Fork the [repository](https://github.com/IvanildoBarauna/currency-quote),
   clone your fork and create a branch from the latest `main`:

   ```sh
   git clone https://github.com/YOUR_USERNAME/currency-quote.git
   cd currency-quote
   git switch -c feat/short-description
   poetry install
   ```

2. Add tests for your change. The suite must be deterministic and offline:
   inject fake repository/validator ports or mock HTTP responses instead of
   calling AwesomeAPI. Cover empty/malformed responses and calendar boundaries
   when changing history; do not assume all weekends lack data.
3. Check formatting, lint, test coverage, lockfile and package build:

   ```sh
   poetry run black --check src/currency_quote src/tests
   poetry run pylint src/currency_quote
   poetry run coverage run -m pytest -q
   poetry run coverage report --fail-under=90
   poetry check --lock
   poetry build
   ```

4. Commit, push and open a PR against `main`. Explain any public API change,
   migration implications, tests and provider behavior you verified manually.
   CI covers Python 3.9–3.13. Avoid mixing unrelated refactors with a fix.

## API and release policy

The proposed v6 client returns `CurrencyQuote` objects with exact `Decimal`
prices; the old `ClientBuilder` still returns eight-key dictionaries, but its
historical prices are now decimal strings. A contract-breaking change needs a
major version and a migration note. Never silently discard a currency pair or
an entire historical range when only one window is empty.

Merge does not publish unconditionally. The publishing workflow requires a
merged PR labeled `deployable`, a configured PyPI token and **manual approval
in the GitHub `Production` environment** before creating a GitHub release and
publishing to PyPI. Do not add the label or alter protection rules casually.

For bugs or feature requests, open a
[GitHub issue](https://github.com/IvanildoBarauna/currency-quote/issues) with
reproduction steps, Python and package versions, and expected/actual results.
Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).
Follow the [Code of Conduct](CODE_OF_CONDUCT.md).
