import asyncio
from unittest.mock import MagicMock, patch

import pytest

from currency_quote import CurrencyQuoteClient
from currency_quote.domain.entities.currency import CurrencyObject, QuoteList
from currency_quote.domain.services.get_currency_quote import GetCurrencyQuoteService

VALIDATE = (
    "currency_quote.domain.services.get_currency_quote.ValidateCurrencyUseCase.execute"
)


def test_validation_is_skipped_when_disabled():
    repository = MagicMock()
    repository.return_value.get_last_quote.return_value = QuoteList()

    service = GetCurrencyQuoteService(
        currency=CurrencyObject(["USD-BRL"]),
        currency_repository=repository,
        validate=False,
    )

    with patch(VALIDATE) as validate:
        service.last()
        validate.assert_not_called()

    repository.assert_called_once()


def test_validation_runs_by_default():
    repository = MagicMock()
    repository.return_value.get_last_quote.return_value = QuoteList()
    currency = CurrencyObject(["USD-BRL"])

    service = GetCurrencyQuoteService(currency=currency, currency_repository=repository)

    with patch(VALIDATE, return_value=currency) as validate:
        service.last()
        validate.assert_called_once()


def test_history_rejects_bad_date_without_touching_repository():
    repository = MagicMock()
    service = GetCurrencyQuoteService(
        currency=CurrencyObject(["USD-BRL"]),
        currency_repository=repository,
        validate=False,
    )

    with pytest.raises(Exception):
        service.history(20991231)

    repository.assert_not_called()


def test_client_accepts_custom_repository():
    repository = MagicMock()
    repository.return_value.get_last_quote.return_value = QuoteList()

    client = CurrencyQuoteClient("USD-BRL", validate=False, repository=repository)
    client.get_last_quote()

    repository.assert_called_once()


def test_async_methods_delegate_to_sync_methods():
    client = CurrencyQuoteClient("USD-BRL", validate=False)
    with patch.object(client, "get_last_quote", return_value=QuoteList()) as last:
        with patch.object(
            client, "get_history_quote", return_value=QuoteList()
        ) as history:
            with patch.object(
                client, "get_history_range", return_value=QuoteList()
            ) as series:

                async def run():
                    await client.get_last_quote_async()
                    await client.get_history_quote_async("2024-06-26")
                    await client.get_history_range_async("2024-06-01", "2024-06-30")

                asyncio.run(run())

    last.assert_called_once_with()
    history.assert_called_once_with("2024-06-26")
    series.assert_called_once_with("2024-06-01", "2024-06-30")
