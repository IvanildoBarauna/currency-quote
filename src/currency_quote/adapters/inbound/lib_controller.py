"""Public entry point of the library."""

import asyncio
from typing import Optional, Type

from currency_quote.application.ports.inbound.controller import IController
from currency_quote.application.ports.outbound.currency_repository import (
    ICurrencyRepository,
)
from currency_quote.application.use_cases.get_history_currency_quote import (
    GetHistCurrencyQuoteUseCase,
)
from currency_quote.application.use_cases.get_last_currency_quote import (
    GetLastCurrencyQuoteUseCase,
)
from currency_quote.config.settings import DEFAULT_REQUEST_CONFIG, RequestConfig
from currency_quote.domain.entities.currency import (
    CurrencyInput,
    CurrencyObject,
    QuoteList,
)
from currency_quote.utils.dates import DateInput


class CurrencyQuoteClient(IController):
    """Fetch currency pair quotes.

    Args:
        currency_list: A single pair (``"USD-BRL"``) or a sequence of pairs
            (``["USD-BRL", "EUR-BRL"]``). Input is normalized, so ``"usd/brl"``
            also works.
        config: Transport settings (retries, timeout, parallelism).
        validate: When ``True`` (default), pairs are checked against the data
            source before quotes are requested. Set to ``False`` to skip that
            extra round-trip once you know your pairs are valid.
        repository: Optional :class:`ICurrencyRepository` implementation, which
            lets you plug in a different data source or a test double.

    Example:
        >>> client = CurrencyQuoteClient("USD-BRL")
        >>> quotes = client.get_last_quote()
        >>> quotes[0].bid_price
        5.4579
    """

    def __init__(
        self,
        currency_list: CurrencyInput,
        config: RequestConfig = DEFAULT_REQUEST_CONFIG,
        validate: bool = True,
        repository: Optional[Type[ICurrencyRepository]] = None,
    ):
        self.currency_list = currency_list
        self.currency_obj = CurrencyObject(currency_list)
        self.config = config
        self.validate = validate
        self.repository = repository

    @property
    def currencies(self) -> list:
        """The normalized currency pairs this client will query."""
        return self.currency_obj.get_currency_list()

    def get_last_quote(self) -> QuoteList:
        """Return the most recent quote for each configured currency pair."""
        return GetLastCurrencyQuoteUseCase.execute(
            currency_obj=self.currency_obj,
            config=self.config,
            validate=self.validate,
            repository=self.repository,
        )

    async def get_last_quote_async(self) -> QuoteList:
        """Fetch current quotes without blocking the caller's event loop.

        Uses a worker thread for the synchronous transport, so cancellation
        does not cancel an in-flight upstream request.
        """
        return await asyncio.to_thread(self.get_last_quote)

    def get_history_quote(self, reference_date: DateInput) -> QuoteList:
        """Return the daily closing quote for a single past date.

        Args:
            reference_date: ``20240626``, ``"2024-06-26"``, or a
                ``date``/``datetime`` object.
        """
        return GetHistCurrencyQuoteUseCase.execute(
            currency_obj=self.currency_obj,
            reference_date=reference_date,
            config=self.config,
            validate=self.validate,
            repository=self.repository,
        )

    async def get_history_quote_async(self, reference_date: DateInput) -> QuoteList:
        """Fetch historical quotes without blocking the caller's event loop."""
        return await asyncio.to_thread(self.get_history_quote, reference_date)

    def get_history_range(
        self,
        start_date: DateInput,
        end_date: Optional[DateInput] = None,
    ) -> QuoteList:
        """Return daily closing quotes for an inclusive date range.

        Args:
            start_date: First day of the range.
            end_date: Last day of the range. Defaults to ``start_date``.
        """
        return GetHistCurrencyQuoteUseCase.execute_range(
            currency_obj=self.currency_obj,
            start_date=start_date,
            end_date=end_date,
            config=self.config,
            validate=self.validate,
            repository=self.repository,
        )

    async def get_history_range_async(
        self,
        start_date: DateInput,
        end_date: Optional[DateInput] = None,
    ) -> QuoteList:
        """Fetch a date range without blocking the caller's event loop."""
        return await asyncio.to_thread(self.get_history_range, start_date, end_date)

    def __repr__(self) -> str:
        return f"CurrencyQuoteClient({self.currencies!r})"


#: Backwards-compatible alias kept for code written against older releases.
ClientBuilder = CurrencyQuoteClient
