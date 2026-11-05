from typing import List
from api_to_dataframe import ClientBuilder, RetryStrategies

from currency_quote.application.ports.outbound.currency_repository import (
    ICurrencyRepository,
)
from currency_quote.config.endpoints import API
from currency_quote.domain.entities.currency import CurrencyQuote, CurrencyObject
from currency_quote.domain.services.validate_reference_date import validate_reference_date
from currency_quote.utils.logger import get_logger

logger = get_logger("currency_api")


class CurrencyAPI(ICurrencyRepository):
    """Repository implementation for fetching currency quotes from external API."""
    def __init__(self, currency_obj: CurrencyObject):
        self.currency_list = currency_obj.get_currency_list()

    def get_last_quote(self) -> List[CurrencyQuote]:
        url = f"{API.ENDPOINT_LAST_COTATION}{','.join(self.currency_list)}"

        client = ClientBuilder(
            endpoint=url, retry_strategy=RetryStrategies.EXPONENTIAL_RETRY_STRATEGY
        )

        response = client.get_api_data()

        quote_list = []

        for item in self.currency_list:
            parsed_item = item.replace("-", "")
            currency_quote = CurrencyQuote(
                currency_pair=item,
                currency_pair_name=response[parsed_item]["name"],
                base_currency_code=response[parsed_item]["code"],
                quote_currency_code=response[parsed_item]["codein"],
                quote_timestamp=int(response[parsed_item]["timestamp"]),
                bid_price=str(response[parsed_item]["bid"]),
                ask_price=str(response[parsed_item]["ask"]),
            )

            quote_list.append(currency_quote)

        return quote_list

    def get_history_quote(self, reference_date: int) -> List[CurrencyQuote]:
        validate_reference_date(reference_date)

        quote_list = []

        for item in self.currency_list:
            url = (f"{API.ENDPOINT_HISTORY_COTATION}{item}"
                   f"?start_date={reference_date}&end_date={reference_date}")

            client = ClientBuilder(
                endpoint=url, retry_strategy=RetryStrategies.EXPONENTIAL_RETRY_STRATEGY
            )

            response = client.get_api_data()

            if not response:
                raise LookupError(f"No quote available for {item} on {reference_date}")

            currency_quote = CurrencyQuote(
                currency_pair=item,
                currency_pair_name=response[0]["name"],
                base_currency_code=response[0]["code"],
                quote_currency_code=response[0]["codein"],
                quote_timestamp=int(response[0]["timestamp"]),
                bid_price=str(response[0]["bid"]),
                ask_price=str(response[0]["ask"]),
            )

            quote_list.append(currency_quote)

        return quote_list
