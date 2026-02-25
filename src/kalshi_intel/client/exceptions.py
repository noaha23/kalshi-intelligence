"""Custom exception hierarchy for Kalshi API errors."""


class KalshiError(Exception):
    """Base exception for all Kalshi client errors."""


class KalshiAPIError(KalshiError):
    """HTTP API returned a non-2xx status."""

    def __init__(
        self,
        status_code: int,
        message: str,
        response_body: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(f"HTTP {status_code}: {message}")


class KalshiAuthError(KalshiAPIError):
    """Authentication failed (401)."""


class KalshiRateLimitError(KalshiAPIError):
    """Rate limit exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
        response_body: dict | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(429, message, response_body)


class KalshiNotFoundError(KalshiAPIError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Not found", response_body: dict | None = None) -> None:
        super().__init__(404, message, response_body)


class KalshiWebSocketError(KalshiError):
    """WebSocket connection or message error."""

    def __init__(self, message: str, error_code: int | None = None) -> None:
        self.error_code = error_code
        super().__init__(message)
