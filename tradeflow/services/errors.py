class UnavailableInBacktestingError(Exception):
    """
    Raised when accessing a service that is not available in backtesting
    """


class CreationError(Exception):
    """
    Raised when accessing a service that failed to be successfully created
    """


class InvalidRequestError(Exception):
    """
    Raised when an invalid request is submitted to a service
    """


class RateLimitError(Exception):
    """
    Raised when an the rate limit has been reached for the given request
    """
