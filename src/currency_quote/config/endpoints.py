class API:
    """AwesomeAPI endpoints and HTTP defaults used by the adapters."""

    __URL__ = "https://economia.awesomeapi.com.br"
    ENDPOINT_AVALIABLE_PARITIES = __URL__ + "/json/available"
    ENDPOINT_LAST_COTATION = __URL__ + "/last/"
    ENDPOINT_HISTORY_COTATION = __URL__ + "/json/daily/"

    HTTP_TIMEOUT_SECONDS = 15.0
    HTTP_RETRY_ATTEMPTS = 3
    HTTP_BACKOFF_BASE_SECONDS = 1.0
    PARITIES_CACHE_TTL_SECONDS = 3600.0
