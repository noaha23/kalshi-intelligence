"""Synchronous REST client for the Kalshi Trade API v2."""

import logging

import httpx

from kalshi_intel.client.auth import KalshiAuthenticator
from kalshi_intel.client.exceptions import (
    KalshiAPIError,
    KalshiAuthError,
    KalshiNotFoundError,
    KalshiRateLimitError,
)
from kalshi_intel.client.models import (
    Balance,
    Candlestick,
    Event,
    EventsResponse,
    Market,
    MarketsResponse,
    Order,
    Orderbook,
    Position,
    TradesResponse,
)
from kalshi_intel.client.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class KalshiRestClient:
    """Synchronous REST client for Kalshi Trade API v2.

    Handles authentication, rate limiting, pagination, and
    deserialization into Pydantic models.
    """

    def __init__(
        self,
        base_url: str,
        authenticator: KalshiAuthenticator,
        read_rate_limit: int = 20,
        write_rate_limit: int = 10,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = authenticator
        self.rate_limiter = RateLimiter(read_rate_limit, write_rate_limit)
        self._client = httpx.Client(timeout=30.0)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "KalshiRestClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    # --- Market Data ---

    def get_markets(
        self,
        *,
        status: str | None = "active",
        series_ticker: str | None = None,
        event_ticker: str | None = None,
        tickers: list[str] | None = None,
        limit: int = 200,
        cursor: str | None = None,
    ) -> MarketsResponse:
        """Fetch markets with optional filters."""
        params: dict = {"limit": limit}
        if status:
            params["status"] = status
        if series_ticker:
            params["series_ticker"] = series_ticker
        if event_ticker:
            params["event_ticker"] = event_ticker
        if tickers:
            params["tickers"] = ",".join(tickers)
        if cursor:
            params["cursor"] = cursor

        data = self._request("GET", "/markets", params=params)
        return MarketsResponse.model_validate(data)

    def get_all_markets(
        self,
        *,
        status: str | None = "active",
        series_ticker: str | None = None,
        event_ticker: str | None = None,
    ) -> list[Market]:
        """Auto-paginate through all matching markets."""
        all_markets: list[Market] = []
        cursor = None

        while True:
            resp = self.get_markets(
                status=status,
                series_ticker=series_ticker,
                event_ticker=event_ticker,
                cursor=cursor,
                limit=1000,
            )
            all_markets.extend(resp.markets)

            if not resp.cursor:
                break
            cursor = resp.cursor

        return all_markets

    def get_market(self, ticker: str) -> Market:
        """Fetch a single market by ticker."""
        data = self._request("GET", f"/markets/{ticker}")
        return Market.model_validate(data.get("market", data))

    def get_events(
        self,
        *,
        status: str | None = None,
        series_ticker: str | None = None,
        limit: int = 200,
        cursor: str | None = None,
    ) -> EventsResponse:
        """Fetch events with optional filters."""
        params: dict = {"limit": limit}
        if status:
            params["status"] = status
        if series_ticker:
            params["series_ticker"] = series_ticker
        if cursor:
            params["cursor"] = cursor

        data = self._request("GET", "/events", params=params)
        return EventsResponse.model_validate(data)

    def get_event(self, event_ticker: str) -> Event:
        """Fetch a single event by ticker."""
        data = self._request("GET", f"/events/{event_ticker}")
        return Event.model_validate(data.get("event", data))

    def get_orderbook(self, ticker: str, depth: int | None = None) -> Orderbook:
        """Fetch current orderbook for a market."""
        params: dict = {}
        if depth:
            params["depth"] = depth
        data = self._request("GET", f"/markets/{ticker}/orderbook", params=params)
        return Orderbook.model_validate({"market_ticker": ticker, **data.get("orderbook", data)})

    def get_trades(
        self,
        *,
        ticker: str | None = None,
        limit: int = 200,
        cursor: str | None = None,
        min_ts: int | None = None,
        max_ts: int | None = None,
    ) -> TradesResponse:
        """Fetch public trade history."""
        params: dict = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        if cursor:
            params["cursor"] = cursor
        if min_ts:
            params["min_ts"] = min_ts
        if max_ts:
            params["max_ts"] = max_ts

        data = self._request("GET", "/markets/trades", params=params)
        return TradesResponse.model_validate(data)

    def get_candlesticks(
        self,
        *,
        series_ticker: str,
        ticker: str,
        period_interval: int = 1440,
        start_ts: int | None = None,
        end_ts: int | None = None,
    ) -> list[Candlestick]:
        """Fetch candlestick data. period_interval: 1, 60, or 1440 minutes."""
        params: dict = {"period_interval": period_interval}
        if start_ts:
            params["start_ts"] = start_ts
        if end_ts:
            params["end_ts"] = end_ts

        data = self._request(
            "GET",
            f"/series/{series_ticker}/markets/{ticker}/candlesticks",
            params=params,
        )
        return [Candlestick.model_validate(c) for c in data.get("candlesticks", [])]

    # --- Portfolio (Authenticated) ---

    def get_balance(self) -> Balance:
        """Fetch account balance."""
        data = self._request("GET", "/portfolio/balance")
        return Balance.model_validate(data)

    def get_positions(
        self,
        *,
        ticker: str | None = None,
        event_ticker: str | None = None,
    ) -> list[Position]:
        """Fetch current positions."""
        params: dict = {}
        if ticker:
            params["ticker"] = ticker
        if event_ticker:
            params["event_ticker"] = event_ticker

        data = self._request("GET", "/portfolio/positions", params=params)
        positions = data.get("market_positions", data.get("positions", []))
        return [Position.model_validate(p) for p in positions]

    def get_orders(
        self,
        *,
        ticker: str | None = None,
        status: str | None = None,
    ) -> list[Order]:
        """Fetch orders."""
        params: dict = {}
        if ticker:
            params["ticker"] = ticker
        if status:
            params["status"] = status

        data = self._request("GET", "/portfolio/orders", params=params)
        return [Order.model_validate(o) for o in data.get("orders", [])]

    # --- Order Management (Authenticated, WRITE operations) ---

    def create_order(
        self,
        *,
        ticker: str,
        side: str,
        action: str,
        count: int,
        yes_price: int | None = None,
        no_price: int | None = None,
        time_in_force: str = "gtc",
    ) -> Order:
        """Place an order. All prices in cents.

        WARNING: This is a WRITE operation. Defaults to demo environment.
        """
        body: dict = {
            "ticker": ticker,
            "side": side,
            "action": action,
            "count": count,
            "type": "limit",
        }
        if yes_price is not None:
            body["yes_price"] = yes_price
        if no_price is not None:
            body["no_price"] = no_price

        data = self._request("POST", "/portfolio/orders", json_body=body, is_write=True)
        return Order.model_validate(data.get("order", data))

    def cancel_order(self, order_id: str) -> None:
        """Cancel a resting order."""
        self._request("DELETE", f"/portfolio/orders/{order_id}", is_write=True)

    # --- Exchange Info ---

    def get_exchange_status(self) -> dict:
        """Get exchange operational status."""
        return self._request("GET", "/exchange/status")

    def get_exchange_schedule(self) -> dict:
        """Get exchange operating schedule."""
        return self._request("GET", "/exchange/schedule")

    # --- Internal ---

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
        is_write: bool = False,
    ) -> dict:
        """Core request method with auth, rate limiting, and error handling."""
        # Rate limit
        if is_write:
            self.rate_limiter.acquire_write()
        else:
            self.rate_limiter.acquire_read()

        # Build full path for signing
        full_path = f"/trade-api/v2{path}"
        url = f"{self.base_url}{path}"

        # Sign request
        headers = self.auth.sign_request(method.upper(), full_path)
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"

        logger.debug(f"{method} {url} params={params}")

        response = self._client.request(
            method,
            url,
            params=params,
            json=json_body,
            headers=headers,
        )

        if response.status_code == 204:
            return {}

        try:
            body = response.json()
        except Exception:
            body = {}

        if response.status_code == 401:
            raise KalshiAuthError(
                status_code=401,
                message=body.get("message", "Authentication failed"),
                response_body=body,
            )
        elif response.status_code == 404:
            raise KalshiNotFoundError(
                message=body.get("message", "Not found"),
                response_body=body,
            )
        elif response.status_code == 429:
            raise KalshiRateLimitError(
                message=body.get("message", "Rate limit exceeded"),
                retry_after=response.headers.get("Retry-After"),
                response_body=body,
            )
        elif response.status_code >= 400:
            raise KalshiAPIError(
                status_code=response.status_code,
                message=body.get("message", f"API error {response.status_code}"),
                response_body=body,
            )

        return body
