# src/tests/test_cache.py
import pytest

from currency_quote.utils.cache import TTLCache


def test_caches_value_within_ttl():
    cache = TTLCache(ttl_seconds=60)
    calls = []

    def fetch():
        calls.append(1)
        return ["USD-BRL"]

    assert cache.get_or_fetch(fetch) == ["USD-BRL"]
    assert cache.get_or_fetch(fetch) == ["USD-BRL"]
    assert len(calls) == 1


def test_refetches_after_ttl_expiry(monkeypatch):
    clock = {"now": 1000.0}
    monkeypatch.setattr(
        "currency_quote.utils.cache.time.monotonic", lambda: clock["now"]
    )

    cache = TTLCache(ttl_seconds=60)
    calls = []

    def fetch():
        calls.append(len(calls))
        return calls

    cache.get_or_fetch(fetch)
    clock["now"] = 1030.0  # still fresh
    cache.get_or_fetch(fetch)
    assert len(calls) == 1

    clock["now"] = 2000.0  # expired
    cache.get_or_fetch(fetch)
    assert len(calls) == 2


def test_clear_forces_refetch():
    cache = TTLCache(ttl_seconds=60)
    calls = []

    def fetch():
        calls.append(1)
        return "value"

    cache.get_or_fetch(fetch)
    cache.clear()
    cache.get_or_fetch(fetch)
    assert len(calls) == 2


def test_non_positive_ttl_raises():
    with pytest.raises(ValueError, match="ttl_seconds"):
        TTLCache(ttl_seconds=0)


def test_fetch_error_is_propagated():
    cache = TTLCache(ttl_seconds=60)

    def broken():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        cache.get_or_fetch(broken)
