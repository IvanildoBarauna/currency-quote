# Guidance for coding agents

This repository is the Python package `currency-quote`. Read [README.md](README.md)
for the public API, [CONTRIBUTING.md](CONTRIBUTING.md) for contribution steps and
[SECURITY.md](SECURITY.md) for vulnerability reports. Work against the current
`main` branch in a separate branch/worktree; do not modify other worktrees.

## Public contract (proposed v6.0.0)

- `CurrencyQuoteClient(pairs)` returns `QuoteList[CurrencyQuote]`. Quote prices
  and optional statistics are `Decimal`; `.to_dict()` returns the eight legacy
  keys with JSON-ready decimal **strings**. `.to_dataframe()` loads pandas
  only if the optional `[pandas]` extra is installed.
- `ClientBuilder(pairs)` remains the dict-returning facade. Its historical
  price fields changed from `float` to strings in v6: this is a **major-release
  migration**, not full v5 behavioral compatibility. Never add fields to its
  eight-key dictionary without a documented contract change.
- Validate dates before HTTP; historical dates must be before today in
  `America/Sao_Paulo`. Treat missing results and invalid/mixed pairs strictly,
  with typed `CurrencyQuoteError` subclasses; do not silently drop a pair.
  Empty history windows are allowed if another window has records. Some
  weekends have records; never infer absence from day of week.
- `CurrencyQuoteClient.get_history_range(start, end)` is inclusive, groups by
  requested pair and orders each pair newest-first. Deduplicate and filter
  provider responses by their local trading dates.

## Architecture and dependencies

`client.py` is the composition root. `adapters/inbound/lib_controller.py` holds
the legacy facade and `__main__.py` the CLI. `application/ports/outbound` defines
repository and validator interfaces; `application/use_cases` depends on these
ports, never on concrete adapters. `domain/` must not import `application/` or
`adapters/`. `adapters/outbound` implements AwesomeAPI parsing and parities
validation; `utils/http.py` supplies shared `requests.Session` pooling,
timeouts and retries. A client-local TTL cache prevents repeated parity calls.
Use provider and validator fakes or mock HTTP responses in tests; no live
network calls in the test suite.

Runtime dependencies are `requests` and `tzdata` (required even on Linux
containers without an IANA database). `pytest` belongs to dev; pandas is an
optional extra. Importing the library must not configure application logging.

## Required validation

```sh
poetry install
poetry run black --check src/currency_quote src/tests
poetry run pylint src/currency_quote
poetry run coverage run -m pytest -q
poetry run coverage report --fail-under=90
poetry check --lock
poetry build
```

Add deterministic regression tests for any provider or contract change,
especially empty/malformed responses, timezone fallback, retries and multi-
window history. CI runs Python 3.9–3.13 plus a quality/build job. Do not claim
a manual smoke test is part of automated CI.

## Release safety

The package version is `6.0.0` in `pyproject.toml` (the prior release is
v5.0.7). Publishing is **not** automatic just because a PR is opened: the
`CD.yaml` workflow only starts publishing after a PR is merged into `main`
with the `deployable` label. The reusable publishing job also requires an
approval in the GitHub `Production` environment before creating the release
and publishing to PyPI. Never remove this approval or apply a release label
without authorization. The automatic Claude Code Review workflow was removed;
`.github/workflows/claude.yml` remains available only by explicit `@claude`
mention.
