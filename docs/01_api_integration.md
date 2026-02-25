# Kalshi API Technical Integration

## Overview

The Kalshi Market Intelligence System integrates with Kalshi's REST API v2 and WebSocket API to retrieve market data, manage portfolio positions, and execute trades on the prediction market exchange. Kalshi is the only CFTC-regulated prediction market exchange in the United States.

### Base URLs

| Environment | REST Base URL | WebSocket URL |
|-------------|--------------|---------------|
| Production | `https://api.elections.kalshi.com/trade-api/v2` | `wss://api.elections.kalshi.com/trade-api/ws/v2` |
| Demo | `https://demo-api.kalshi.co/trade-api/v2` | `wss://demo-api.kalshi.co/trade-api/ws/v2` |

All HTTP requests use JSON request and response bodies with cent-denominated integers for all monetary values. The demo environment mirrors production behavior but operates with paper money, making it suitable for development and testing. Configure the environment via the `KALSHI_ENVIRONMENT` env var (`demo` or `production`).

---

## Authentication: RSA-PSS SHA-256

Kalshi uses RSA-PSS SHA-256 signature-based authentication. Every authenticated request must include three custom headers.

### Required Headers

| Header | Value |
|--------|-------|
| `KALSHI-ACCESS-KEY` | Your API key identifier (public portion, from Kalshi dashboard) |
| `KALSHI-ACCESS-SIGNATURE` | Base64-encoded RSA-PSS SHA-256 signature of the request message |
| `KALSHI-ACCESS-TIMESTAMP` | Current UTC timestamp in milliseconds (epoch time) |

### Signature Construction

The signature message is constructed by concatenating three components with no delimiter:

```
message = "{timestamp_ms}{METHOD}{path_without_query}"
```

- `timestamp_ms`: The same millisecond-precision UTC epoch timestamp sent in the `KALSHI-ACCESS-TIMESTAMP` header.
- `METHOD`: The uppercase HTTP method (e.g., `GET`, `POST`, `DELETE`).
- `path_without_query`: The request path starting from `/trade-api/v2/...`, excluding any query string parameters.

**Example message:**

For a GET request to `/trade-api/v2/markets?status=active` at timestamp `1700000000000`:

```
1700000000000GET/trade-api/v2/markets
```

Note that query parameters (`?status=active`) are stripped from the path before signing.

### Signing Process

The message is signed using RSA-PSS with the following parameters:

- **Hash algorithm:** SHA-256
- **Padding:** PSS (Probabilistic Signature Scheme)
- **Salt length:** Maximum available (typically equal to hash length, 32 bytes)
- **Private key format:** PEM-encoded RSA private key

The resulting binary signature is Base64-encoded before being placed in the `KALSHI-ACCESS-SIGNATURE` header.

### Key Setup

1. Generate an RSA key pair: `openssl genrsa -out kalshi_private.pem 4096`
2. Extract the public key: `openssl rsa -in kalshi_private.pem -pubout -out kalshi_public.pem`
3. Upload the public key to your Kalshi account settings dashboard
4. Store the private key path and key ID in environment variables:

```
KALSHI_API_KEY_ID=<your-key-id>
KALSHI_PRIVATE_KEY_PATH=./keys/kalshi_private.pem
```

The private key grants full account access. Never commit it to version control. The `.gitignore` excludes `keys/`.

### WebSocket Authentication

WebSocket connections use the same signature scheme but with a fixed path during the HTTP upgrade handshake:

```
message = "{timestamp_ms}GET/trade-api/ws/v2"
```

---

## Key Endpoints

### Market Data (Public, READ)

| Endpoint | Method | Description | Client Method |
|----------|--------|-------------|---------------|
| `/markets` | GET | List markets with filters (status, series_ticker, event_ticker, cursor, limit) | `get_markets()` |
| `/markets/{ticker}` | GET | Single market detail by ticker | `get_market(ticker)` |
| `/events` | GET | List events (groups of related markets) | `get_events()` |
| `/events/{event_ticker}` | GET | Single event and its child markets | `get_event(ticker)` |
| `/markets/{ticker}/orderbook` | GET | Current orderbook (bids and asks) | `get_orderbook(ticker)` |
| `/markets/trades` | GET | Public trade history | `get_trades()` |
| `/series/{series_ticker}` | GET | Get a series (recurring event group) | `get_series(ticker)` |
| `/series/{s}/markets/{t}/candlesticks` | GET | OHLCV candlestick data | `get_candlesticks()` |
| `/exchange/status` | GET | Exchange operational status | `get_exchange_status()` |
| `/exchange/schedule` | GET | Operating schedule | `get_exchange_schedule()` |

**Market object key fields:**

- `ticker` - Unique market identifier (e.g., `INXD-25FEB21-T5612`)
- `event_ticker` - Parent event identifier
- `yes_bid` / `yes_ask` - Current best bid and ask prices for YES contracts (in cents, 1-99)
- `no_bid` / `no_ask` - Current best bid and ask prices for NO contracts
- `volume` / `volume_24h` - Total and 24-hour trading volume
- `open_interest` - Number of outstanding contracts
- `close_time` - ISO 8601 timestamp when the market closes
- `status` - One of: `open`, `closed`, `settled`
- `result` - Settlement result: `yes`, `no`, or `null` if unsettled

**Candlestick intervals:** `1` (1 minute), `60` (1 hour), `1440` (1 day).

### Portfolio Management (Authenticated, READ)

| Endpoint | Method | Description | Client Method |
|----------|--------|-------------|---------------|
| `/portfolio/balance` | GET | Current account balance and portfolio value | `get_balance()` |
| `/portfolio/positions` | GET | All open positions with average entry price and quantity | `get_positions()` |
| `/portfolio/orders` | GET | Order history (open, filled, cancelled) | `get_orders()` |

### Order Management (Authenticated, WRITE)

| Endpoint | Method | Description | Client Method |
|----------|--------|-------------|---------------|
| `/portfolio/orders` | POST | Place a new order | `create_order()` |
| `/portfolio/orders/{order_id}` | DELETE | Cancel an open resting order | `cancel_order()` |

**Order placement parameters:**

```json
{
  "ticker": "INXD-25FEB21-T5612",
  "action": "buy",
  "side": "yes",
  "type": "limit",
  "count": 10,
  "yes_price": 55
}
```

- `action`: `buy` or `sell`
- `side`: `yes` or `no`
- `type`: `limit` or `market`
- `count`: Number of contracts
- `yes_price`: Limit price in cents (1-99) for the YES side

---

## Rate Limits

Kalshi enforces per-user rate limits using a token bucket algorithm.

### Tier Limits

| Tier | Read/s | Write/s | Notes |
|------|--------|---------|-------|
| Basic | 20 | 10 | Default for all accounts |
| Advanced | 30 | 30 | Request upgrade from Kalshi |
| Premier | 100 | 100 | High-volume traders |
| Prime | 400 | 400 | Institutional / market makers |

When the rate limit is exceeded, the API returns HTTP 429 (Too Many Requests) with a `Retry-After` header indicating how many seconds to wait.

### Rate Limit Strategy

The client implements a dual token-bucket rate limiter with separate buckets for reads and writes:

1. **Pre-request throttling** using a token bucket that tracks available capacity per second. When tokens are exhausted, the limiter blocks (up to a configurable timeout) rather than throwing immediately, preventing accidental 429 errors.
2. **Exponential backoff** on 429 responses, starting at 1 second and doubling up to a maximum of 30 seconds.
3. **Request batching** where possible (e.g., fetching markets in pages rather than individually).

---

## WebSocket API

Real-time market data is available via the WebSocket endpoint for streaming price updates, trade executions, and order book changes.

### Connection

```
wss://api.elections.kalshi.com/trade-api/ws/v2
```

Authentication is performed during the HTTP upgrade handshake using the same three headers.

### Subscription Channels

After connecting, subscribe to channels by sending JSON messages:

```json
{
  "id": 1,
  "cmd": "subscribe",
  "params": {
    "channels": ["orderbook_delta"],
    "market_tickers": ["INXD-25FEB21-T5612"]
  }
}
```

| Channel | Auth Required | Description |
|---------|--------------|-------------|
| `ticker` | No | Price/volume updates |
| `trade` | No | Public trade feed |
| `market_lifecycle_v2` | No | Market status changes |
| `multivariate` | No | Multi-outcome event updates |
| `orderbook_delta` | Yes | Orderbook level changes |
| `fill` | Yes | Your order fills |
| `market_positions` | Yes | Your position changes |
| `communications` | Yes | System messages |

### Heartbeat

The server sends periodic ping frames. The client must respond with pong frames to maintain the connection. If no pong is received within 30 seconds, the server closes the connection.

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Handling |
|------|---------|----------|
| 200 | Success | Process response body |
| 400 | Bad Request | Check request parameters; do not retry |
| 401 | Unauthorized | Verify API key, timestamp clock skew, and signature construction |
| 403 | Forbidden | Insufficient permissions for the requested resource |
| 404 | Not Found | Market ticker or resource does not exist |
| 429 | Rate Limited | Back off and retry after the `Retry-After` duration |
| 500 | Server Error | Retry with exponential backoff (max 3 retries) |

### Common 401 Causes

1. **Clock skew**: The timestamp in `KALSHI-ACCESS-TIMESTAMP` is more than 10 seconds from server time. Ensure the system clock is synchronized via NTP.
2. **Wrong path in signature**: The path used in signature construction must match the actual request path exactly, without query parameters.
3. **Incorrect key format**: The private key must be a valid PEM-encoded RSA key.
4. **Wrong key ID**: The `KALSHI-ACCESS-KEY` must match the key ID displayed in the Kalshi dashboard for the uploaded public key.

### Typed Exceptions

The client raises typed exceptions for precise error handling:

| Exception | HTTP Code | When |
|-----------|-----------|------|
| `KalshiAuthError` | 401 | Bad signature, expired key, wrong key ID |
| `KalshiNotFoundError` | 404 | Invalid ticker or resource |
| `KalshiRateLimitError` | 429 | Rate limit exceeded |
| `KalshiAPIError` | 4xx/5xx | Any other API error |
| `KalshiWebSocketError` | N/A | WebSocket connection issues |

---

## Pagination

All list endpoints use cursor-based pagination with opaque cursor strings (not page numbers).

**Request parameters:**

- `limit` (integer): Maximum number of results per page (default 100, max 1000).
- `cursor` (string): Opaque cursor from the previous response to fetch the next page.

**Response structure:**

```json
{
  "cursor": "eyJsYXN0X2lkIjo...",
  "markets": [ ... ]
}
```

**Iteration pattern:**

1. Make the initial request without a cursor.
2. If the response includes a non-empty `cursor`, make another request with that cursor value.
3. Repeat until the cursor is empty or absent.

The client provides auto-pagination helpers (e.g., `get_all_markets()`) that iterate through all pages transparently.

---

## Our Implementation

The system's API integration is organized into three primary classes.

### KalshiAuthenticator

Located in `src/kalshi_intel/client/auth.py`. Handles all authentication concerns:

- Loads the RSA private key from the PEM file specified by `KALSHI_PRIVATE_KEY_PATH`.
- Constructs the signature message from timestamp, method, and path.
- Signs the message using RSA-PSS with SHA-256.
- Returns the three required authentication headers as a dictionary.

```python
def sign_request(self, method: str, path: str, timestamp_ms: int | None = None) -> dict[str, str]:
    if timestamp_ms is None:
        timestamp_ms = self._current_timestamp_ms()

    path_without_query = path.split("?")[0]
    message = f"{timestamp_ms}{method.upper()}{path_without_query}"
    signature = self._sign(message)

    return {
        "KALSHI-ACCESS-KEY": self.api_key_id,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": str(timestamp_ms),
    }
```

### KalshiRestClient

Wraps `httpx` (async HTTP client) with Kalshi-specific behavior:

- Automatically injects authentication headers on every request via `KalshiAuthenticator`.
- Implements rate limiting with the dual token-bucket to stay within API limits.
- Provides typed methods for each endpoint (e.g., `get_markets()`, `get_market()`, `get_balance()`, `place_order()`).
- Handles pagination transparently with auto-pagination helpers that yield markets across pages.
- Retries on transient errors (429, 500) with exponential backoff.
- Supports both production and demo environments, selected by configuration.
- Deserializes all API responses into Pydantic v2 models.

### KalshiWebSocketClient

Located in `src/kalshi_intel/client/websocket.py`. Manages a persistent WebSocket connection for real-time data:

- Authenticates during the WebSocket handshake.
- Supports subscribing and unsubscribing to channels for specific market tickers.
- Dispatches incoming messages to registered callback handlers.
- Implements automatic reconnection with exponential backoff on disconnection.
- Sends pong responses to server ping frames to maintain the connection.

```python
ws = KalshiWebSocketClient(settings.ws_url, authenticator=auth)
await ws.connect()
await ws.subscribe(["ticker", "trade"], market_tickers=["ECON-CPI-25MAR"])

async for msg in ws.listen():
    print(msg["type"], msg.get("msg"))
```

---

## Data Models

All API responses are deserialized into Pydantic v2 models (`src/kalshi_intel/client/models.py`). Key computed properties:

```python
class Market(BaseModel):
    ticker: str
    yes_bid: int = 0      # cents
    yes_ask: int = 0      # cents
    volume_24h: int = 0
    open_interest: int = 0

    @property
    def mid_price_cents(self) -> float:
        if self.yes_bid and self.yes_ask:
            return (self.yes_bid + self.yes_ask) / 2.0
        return float(self.last_price)

    @property
    def implied_probability(self) -> float:
        return self.mid_price_cents / 100.0
```

---

## Configuration

All API configuration is managed through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `KALSHI_API_KEY_ID` | API key identifier | (required) |
| `KALSHI_PRIVATE_KEY_PATH` | Path to RSA private key PEM file | (required) |
| `KALSHI_ENVIRONMENT` | `demo` or `production` | `demo` |
| `KALSHI_API_BASE_URL` | Base URL override | Derived from environment |
| `KALSHI_MAX_RETRIES` | Maximum retry attempts on transient errors | `3` |
| `KALSHI_READ_RATE_LIMIT` | Read requests per second | `20` |
| `KALSHI_WRITE_RATE_LIMIT` | Write requests per second | `10` |

---

## Risks and Considerations

- **Key security.** The RSA private key grants full account access. Never commit it to version control.
- **Clock drift.** Signature timestamps are validated server-side. If your system clock drifts more than a few seconds, authentication will fail. Use NTP.
- **Rate limit exhaustion.** The daily scanner fetches orderbooks for each filtered market (one API call per market). With 200+ passing markets, this can take several minutes and approach rate limits.
- **API changes.** Kalshi occasionally modifies endpoints or field names. Monitor changelogs.
- **Demo vs production divergence.** Demo market prices, volumes, and orderbook depth do not reflect production. Strategies validated on demo may not transfer.
- **Monetary precision.** All calculations use integer cents to avoid floating-point errors. Be careful when converting to/from dollar amounts.
- **Never use production keys in development.** The `KALSHI_ENVIRONMENT` setting defaults to `demo` for safety.
