class API:
    __URL__ = "https://economia.awesomeapi.com.br"
    ENDPOINT_AVALIABLE_PARITIES = __URL__ + "/json/available"
    ENDPOINT_LAST_COTATION = __URL__ + "/last/"
    ENDPOINT_HISTORY_COTATION = __URL__ + "/json/daily/"
    RETRY_TIME_SECONDS = 2
    RETRY_ATTEMPTS = 3
    # Seconds the list of available currency pairs stays cached in memory.
    AVAILABLE_PARITIES_TTL_SECONDS = 3600
    # The daily endpoint never returns more than 360 records per request.
    HISTORY_MAX_RECORDS = 360
    # Calendar-day window per request. 360 calendar days yield at most ~250
    # business days, keeping every chunk comfortably under HISTORY_MAX_RECORDS.
    HISTORY_CHUNK_DAYS = 360
