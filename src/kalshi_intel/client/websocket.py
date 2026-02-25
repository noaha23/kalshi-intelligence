"""WebSocket client for real-time Kalshi market data.

Channels (public):  ticker, trade, market_lifecycle_v2, multivariate
Channels (private): orderbook_delta, fill, market_positions, communications
"""

import json
import logging
from collections.abc import AsyncIterator, Callable

import websockets

from kalshi_intel.client.auth import KalshiAuthenticator
from kalshi_intel.client.exceptions import KalshiWebSocketError

logger = logging.getLogger(__name__)


class KalshiWebSocketClient:
    """WebSocket client for real-time Kalshi market data."""

    def __init__(
        self,
        ws_url: str,
        authenticator: KalshiAuthenticator | None = None,
    ) -> None:
        self.ws_url = ws_url
        self.auth = authenticator
        self._ws = None
        self._msg_id = 0

    async def connect(self) -> None:
        """Establish WebSocket connection with optional authentication."""
        extra_headers = {}
        if self.auth:
            extra_headers = self.auth.sign_websocket()

        self._ws = await websockets.connect(
            self.ws_url,
            additional_headers=extra_headers,
            ping_interval=10,
            ping_timeout=30,
        )
        logger.info(f"Connected to {self.ws_url}")

    async def subscribe(
        self,
        channels: list[str],
        market_tickers: list[str] | None = None,
    ) -> None:
        """Subscribe to one or more channels.

        Args:
            channels: Channel names (e.g., ["ticker", "trade"])
            market_tickers: Specific market tickers to subscribe to.
                           Omit to subscribe to all markets.
        """
        if not self._ws:
            raise KalshiWebSocketError("Not connected. Call connect() first.")

        self._msg_id += 1
        msg: dict = {
            "id": self._msg_id,
            "cmd": "subscribe",
            "params": {"channels": channels},
        }
        if market_tickers:
            if len(market_tickers) == 1:
                msg["params"]["market_ticker"] = market_tickers[0]
            else:
                msg["params"]["market_tickers"] = market_tickers

        await self._ws.send(json.dumps(msg))
        logger.info(f"Subscribed to {channels} for {market_tickers or 'all markets'}")

    async def unsubscribe(
        self,
        channels: list[str],
        market_tickers: list[str] | None = None,
    ) -> None:
        """Unsubscribe from channels."""
        if not self._ws:
            return

        self._msg_id += 1
        msg: dict = {
            "id": self._msg_id,
            "cmd": "unsubscribe",
            "params": {"channels": channels},
        }
        if market_tickers:
            msg["params"]["market_tickers"] = market_tickers

        await self._ws.send(json.dumps(msg))

    async def listen(self) -> AsyncIterator[dict]:
        """Yield parsed messages as they arrive."""
        if not self._ws:
            raise KalshiWebSocketError("Not connected. Call connect() first.")

        try:
            async for raw in self._ws:
                try:
                    data = json.loads(raw)
                    yield data
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse WebSocket message: {raw[:100]}")
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e}")
            raise KalshiWebSocketError(f"Connection closed: {e}", error_code=e.code) from e

    async def listen_tickers(
        self,
        market_tickers: list[str],
        callback: Callable[[str, int, int, int], None],
    ) -> None:
        """Subscribe to ticker channel and invoke callback on updates.

        Callback args: (market_ticker, yes_bid, yes_ask, volume)
        """
        await self.subscribe(["ticker"], market_tickers)

        async for msg in self.listen():
            msg_type = msg.get("type")
            if msg_type == "ticker":
                data = msg.get("msg", {})
                ticker = data.get("market_ticker", "")
                yes_bid = data.get("yes_bid", 0)
                yes_ask = data.get("yes_ask", 0)
                volume = data.get("volume", 0)
                callback(ticker, yes_bid, yes_ask, volume)

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self._ws:
            await self._ws.close()
            self._ws = None
            logger.info("WebSocket connection closed")
