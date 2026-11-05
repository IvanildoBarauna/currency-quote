"""HTTP error contract, configuration and logging import behavior."""

import json
import logging
import os
import subprocess
import sys
from unittest.mock import Mock

import pytest
import requests

from currency_quote.exceptions import CurrencyAPIError, InvalidConfigError
from currency_quote.utils.http import HTTPClient, HTTPConfig


def test_zero_retries_still_performs_first_request_and_propagates_timeout():
    session = Mock(spec=requests.Session)
    response = Mock()
    response.json.return_value = {"ok": True}
    session.get.return_value = response
    client = HTTPClient(HTTPConfig(timeout=0.1, retries=0), session=session)
    assert client.get("https://example.test/json") == {"ok": True}
    session.get.assert_called_once_with("https://example.test/json", timeout=0.1)
    client.close()
    session.close.assert_not_called()


def test_own_session_configures_status_retry_and_closes():
    client = HTTPClient(HTTPConfig(retries=0))
    assert client.session.get_adapter("https://example.test").max_retries.total == 0
    assert (
        429
        in client.session.get_adapter(
            "https://example.test"
        ).max_retries.status_forcelist
    )
    client.close()


@pytest.mark.parametrize(
    "failure",
    [requests.Timeout(), requests.ConnectionError(), ValueError("invalid JSON")],
)
def test_transport_errors_are_typed(failure):
    session = Mock(spec=requests.Session)
    session.get.side_effect = failure
    with pytest.raises(CurrencyAPIError):
        HTTPClient(HTTPConfig(), session=session).get("https://example.test")


def test_http_error_has_status_code():
    session = Mock(spec=requests.Session)
    response = requests.Response()
    response.status_code = 429
    session.get.return_value = response
    with pytest.raises(CurrencyAPIError) as exc:
        HTTPClient(HTTPConfig(), session=session).get("https://example.test")
    assert exc.value.status_code == 429


def test_import_does_not_modify_root_or_configure_package_stream():
    code = "import logging, json; before=logging.getLogger().level; import currency_quote; root=logging.getLogger(); p=logging.getLogger('currency_quote'); print(json.dumps([before, root.level, [type(h).__name__ for h in p.handlers]]))"
    process = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    before, after, handlers = json.loads(process.stdout)
    assert before == after
    assert handlers == ["NullHandler"]


def test_import_without_system_timezone_database():
    """A minimal container can depend exclusively on the bundled tzdata package."""
    code = (
        "from zoneinfo import TZPATH; assert not TZPATH; "
        "import currency_quote; "
        "from currency_quote.utils.dates import PROVIDER_TIMEZONE; "
        "print(PROVIDER_TIMEZONE.key)"
    )
    process = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYTHONTZPATH": ""},
    )
    assert process.stdout.strip() == "America/Sao_Paulo"


@pytest.mark.parametrize(
    "kwargs", [{"retries": -1}, {"timeout": 0}, {"timeout": True}, {"retries": 1.5}]
)
def test_invalid_configuration_is_a_library_error(kwargs):
    with pytest.raises(InvalidConfigError):
        HTTPConfig(**kwargs)
