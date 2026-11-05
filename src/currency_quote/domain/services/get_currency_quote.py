"""Domain service orchestrating validation and quote retrieval."""

from typing import Optional, Type

from currency_quote.application.ports.outbound.currency_repository import (
    ICurrencyRepository,
)
from currency_quote.application.use_cases.validate_currency import (
    ValidateCurrencyUseCase,
)
from currency_quote.config.settings import DEFAULT_REQUEST_CONFIG, RequestConfig
from currency_quote.domain.entities.currency import CurrencyObject, QuoteList
from currency_quote.utils.dates import DateInput, validate_past_date


class GetCurrencyQuoteService:
    """Fetches quotes through an injected repository.

    Args:
        currency: The requested currency pairs.
        currency_repository: Concrete :class:`ICurrencyRepository` implementation.
        config: Transport settings forwarded to the repository.
        validate: When ``True`` (default), currency pairs are checked against
            the data source before quotes are requested. Disabling it removes
            one HTTP round-trip per call.
    """

    def __init__(
        self,
        currency: CurrencyObject,
        currency_repository: Type[ICurrencyRepository],
        config: RequestConfig = DEFAULT_REQUEST_CONFIG,
        validate: bool = True,
    ):
        self.currency = currency
        self.currency_repository = currency_repository
        self.config = config
        self.validate = validate

    def last(self) -> QuoteList:
        return self._repository().get_last_quote()

    def history(self, reference_date: DateInput) -> QuoteList:
        # Fail fast on a bad date before spending any network call.
        reference_date = validate_past_date(reference_date)
        return self._repository().get_history_quote(reference_date=reference_date)

    def history_range(
        self,
        start_date: DateInput,
        end_date: Optional[DateInput] = None,
    ) -> QuoteList:
        start_date = validate_past_date(start_date)
        if end_date is not None:
            end_date = validate_past_date(end_date)
        return self._repository().get_history_quote_range(
            start_date=start_date, end_date=end_date
        )

    def validate_currency_code(self) -> CurrencyObject:
        if not self.validate:
            return self.currency
        return ValidateCurrencyUseCase.execute(self.currency, config=self.config)

    def _repository(self) -> ICurrencyRepository:
        return self.currency_repository(self.validate_currency_code(), self.config)
