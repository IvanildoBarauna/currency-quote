import pytest
from currency_quote.adapters.outbound.currency_validator_api import PARITIES_CACHE


@pytest.fixture(autouse=True)
def clear_parities_cache():
    """Isolate tests from the module-level parities TTL cache."""
    PARITIES_CACHE.clear()
    yield
    PARITIES_CACHE.clear()


@pytest.fixture
def mock_currency_api_response():
    """Mock response for currency API."""
    return {
        "USDBRL": {
            "code": "USD",
            "codein": "BRL",
            "name": "Dólar Americano/Real Brasileiro",
            "high": "5.1234",
            "low": "5.0432",
            "varBid": "0.0123",
            "pctChange": "0.24",
            "bid": "5.0876",
            "ask": "5.0891",
            "timestamp": "1614024000",
            "create_date": "2023-01-01 13:00:00",
        },
        "EURBRL": {
            "code": "EUR",
            "codein": "BRL",
            "name": "Euro/Real Brasileiro",
            "high": "6.1234",
            "low": "6.0432",
            "varBid": "0.0223",
            "pctChange": "0.37",
            "bid": "6.0876",
            "ask": "6.0891",
            "timestamp": "1614024000",
            "create_date": "2023-01-01 13:00:00",
        },
    }


@pytest.fixture
def mock_currency_history_api_response():
    """Mock response for currency history API."""
    return [
        {
            "code": "USD",
            "codein": "BRL",
            "name": "Dólar Americano/Real Brasileiro",
            "high": "5.1234",
            "low": "5.0432",
            "varBid": "0.0123",
            "pctChange": "0.24",
            "bid": "5.0876",
            "ask": "5.0891",
            "timestamp": "1614024000",
            "create_date": "2022-06-21 13:00:00",
        }
    ]


@pytest.fixture
def mock_validator_api_response():
    """Mock response for currency validator API."""
    return ["USD-BRL", "EUR-BRL", "USD-BRLT"]
