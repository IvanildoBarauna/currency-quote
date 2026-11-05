from typing import Union
from currency_quote.application.ports.inbound.controller import IController
from currency_quote.application.use_cases.get_last_currency_quote import (
    GetLastCurrencyQuoteUseCase,
)
from currency_quote.application.use_cases.get_history_currency_quote import (
    GetHistCurrencyQuoteUseCase,
)
from currency_quote.domain.entities.currency import CurrencyObject
from currency_quote.domain.services.validate_reference_date import validate_reference_date


class ClientBuilder(IController):
    def __init__(self, currency_list: Union[list, str]):
        self.currency_list = currency_list
        self.currency_obj = CurrencyObject(self.currency_list)

    def get_last_quote(self) -> list:
        use_case_result = GetLastCurrencyQuoteUseCase.execute(
            currency_obj=self.currency_obj
        )

        controller_return = []

        for item in use_case_result:
            dic = {
                "currency_pair": item.currency_pair,
                "currency_pair_name": item.currency_pair_name,
                "base_currency_code": item.base_currency_code,
                "quote_currency_code": item.quote_currency_code,
                "quote_timestamp": item.quote_timestamp,
                "bid_price": item.bid_price,
                "ask_price": item.ask_price,
                "quote_extracted_at": item.quote_extracted_at,
            }

            controller_return.append(dic)

        return controller_return

    def get_history_quote(self, reference_date: int) -> list:
        validate_reference_date(reference_date)
        use_case_result = GetHistCurrencyQuoteUseCase.execute(
            currency_obj=self.currency_obj,
            reference_date=reference_date,
        )

        use_case_result_parsed = []

        for item in use_case_result:
            dic = {
                "currency_pair": item.currency_pair,
                "currency_pair_name": item.currency_pair_name,
                "base_currency_code": item.base_currency_code,
                "quote_currency_code": item.quote_currency_code,
                "quote_timestamp": item.quote_timestamp,
                "bid_price": item.bid_price,
                "ask_price": item.ask_price,
                "quote_extracted_at": item.quote_extracted_at,
            }

            use_case_result_parsed.append(dic)

        return use_case_result_parsed
