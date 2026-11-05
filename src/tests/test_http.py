# src/tests/test_http.py
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests

from currency_quote.exceptions import CurrencyAPIError
from currency_quote.utils.http import HTTPConfig, get_json

URL = "https://economia.awesomeapi.com.br/json/available"


def make_response(payload=None, status=200, json_error=None):
    response = MagicMock(status_code=status)
    if json_error is not None:
        response.json.side_effect = json_error
    else:
        response.json.return_value = payload if payload is not None else {}
    if status >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(
            f"HTTP {status}", response=SimpleNamespace(status_code=status)
        )
    else:
        response.raise_for_status.return_value = None
    return response


def test_success_returns_payload():
    payload = {"USD-BRL": "Dólar"}
    with patch(
        "currency_quote.utils.http.requests.get", return_value=make_response(payload)
    ):
        assert get_json(URL) == payload


@patch("currency_quote.utils.http.requests.get")
@patch("currency_quote.utils.http.time.sleep")
def test_retries_on_server_error_then_succeeds(mock_sleep, mock_get):
    mock_get.side_effect = [
        make_response(status=500),
        make_response(status=500),
        make_response({"ok": True}),
    ]
    assert get_json(URL) == {"ok": True}
    assert mock_get.call_count == 3
    assert [call.args[0] for call in mock_sleep.call_args_list] == [1, 2]


@patch("currency_quote.utils.http.requests.get")
def test_client_error_is_not_retried(mock_get):
    mock_get.return_value = make_response(status=404)
    with pytest.raises(CurrencyAPIError, match="HTTP 404"):
        get_json(URL)
    assert mock_get.call_count == 1


@patch("currency_quote.utils.http.requests.get")
@patch("currency_quote.utils.http.time.sleep")
def test_connection_error_retries_until_exhaustion(mock_sleep, mock_get):
    mock_get.side_effect = requests.ConnectionError("nope")
    with pytest.raises(CurrencyAPIError, match="unreachable after 3 attempt"):
        get_json(URL)
    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 2


@patch("currency_quote.utils.http.requests.get")
@patch("currency_quote.utils.http.time.sleep")
def test_timeout_is_retried(mock_sleep, mock_get):
    mock_get.side_effect = [requests.Timeout("slow"), make_response({"ok": 1})]
    assert get_json(URL) == {"ok": 1}
    assert mock_get.call_count == 2
    assert mock_sleep.call_count == 1


@patch("currency_quote.utils.http.requests.get")
def test_invalid_json_raises_without_retry(mock_get):
    mock_get.return_value = make_response(
        json_error=json.JSONDecodeError("bad", "<doc>", 0)
    )
    with pytest.raises(CurrencyAPIError, match="did not return valid JSON"):
        get_json(URL)
    assert mock_get.call_count == 1


def test_http_config_rejects_bad_values():
    with pytest.raises(ValueError, match="timeout_seconds"):
        HTTPConfig(timeout_seconds=0)
    with pytest.raises(ValueError, match="retry_attempts"):
        HTTPConfig(retry_attempts=0)


def test_http_config_defaults():
    config = HTTPConfig()
    assert config.timeout_seconds > 0
    assert config.retry_attempts >= 1
