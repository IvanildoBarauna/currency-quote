import pytest
from api_to_dataframe import RetryStrategies

from currency_quote.config.settings import (
    DEFAULT_REQUEST_CONFIG,
    RequestConfig,
    RetryStrategy,
)


def test_default_config_values():
    assert DEFAULT_REQUEST_CONFIG.retry_strategy is RetryStrategy.EXPONENTIAL
    assert DEFAULT_REQUEST_CONFIG.retries == 3
    assert DEFAULT_REQUEST_CONFIG.timeout == 10


def test_as_client_kwargs_maps_to_transport():
    config = RequestConfig(
        retry_strategy=RetryStrategy.LINEAR, retries=5, initial_delay=2, timeout=30
    )
    kwargs = config.as_client_kwargs()

    assert kwargs == {
        "retry_strategy": RetryStrategies.LINEAR_RETRY_STRATEGY,
        "retries": 5,
        "initial_delay": 2,
        "connection_timeout": 30,
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"retries": -1},
        {"initial_delay": -1},
        {"timeout": 0},
        {"max_workers": 0},
    ],
)
def test_invalid_config_is_rejected(kwargs):
    with pytest.raises(ValueError):
        RequestConfig(**kwargs)


def test_config_is_immutable():
    with pytest.raises(Exception):
        DEFAULT_REQUEST_CONFIG.retries = 99
