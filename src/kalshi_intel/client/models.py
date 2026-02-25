"""Pydantic v2 models for Kalshi API responses.

All monetary values from the API arrive as FixedPointDollars strings (e.g., "0.5200").
Computed properties convert to cents (integers) for all calculations.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class MarketStatus(StrEnum):
    INITIALIZED = "initialized"
    INACTIVE = "inactive"
    ACTIVE = "active"
    CLOSED = "closed"
    DETERMINED = "determined"
    FINALIZED = "finalized"


class OrderSide(StrEnum):
    YES = "yes"
    NO = "no"


class OrderAction(StrEnum):
    BUY = "buy"
    SELL = "sell"


class TimeInForce(StrEnum):
    FILL_OR_KILL = "fill_or_kill"
    GOOD_TILL_CANCELED = "good_till_canceled"
    IMMEDIATE_OR_CANCEL = "immediate_or_cancel"


class StrikeType(StrEnum):
    GREATER = "greater"
    LESS = "less"
    BETWEEN = "between"
    FUNCTIONAL = "functional"
    CUSTOM = "custom"
    STRUCTURED = "structured"


def _dollars_to_cents(dollars_str: str) -> int:
    """Convert FixedPointDollars string to integer cents."""
    try:
        return round(float(dollars_str) * 100)
    except (ValueError, TypeError):
        return 0


class Market(BaseModel):
    """A single Kalshi market (binary contract)."""

    ticker: str
    event_ticker: str
    market_type: str = "binary"
    yes_sub_title: str = ""
    no_sub_title: str = ""
    status: MarketStatus = MarketStatus.ACTIVE
    open_time: datetime | None = None
    close_time: datetime | None = None
    expected_expiration_time: datetime | None = None
    yes_bid: int = 0  # cents
    yes_ask: int = 0  # cents
    no_bid: int = 0  # cents
    no_ask: int = 0  # cents
    last_price: int = 0  # cents
    previous_yes_bid: int = 0
    previous_yes_ask: int = 0
    previous_price: int = 0
    volume: int = 0
    volume_24h: int = 0
    open_interest: int = 0
    result: str = ""
    rules_primary: str = ""
    rules_secondary: str = ""
    strike_type: StrikeType | None = None
    floor_strike: float | None = None
    cap_strike: float | None = None
    category: str = ""
    series_ticker: str = ""
    subtitle: str = ""
    title: str = ""

    @property
    def mid_price_cents(self) -> float:
        """Midpoint of yes bid/ask in cents."""
        if self.yes_bid and self.yes_ask:
            return (self.yes_bid + self.yes_ask) / 2.0
        return float(self.last_price)

    @property
    def spread_cents(self) -> int:
        """Ask minus bid in cents."""
        if self.yes_bid and self.yes_ask:
            return self.yes_ask - self.yes_bid
        return 0

    @property
    def implied_probability(self) -> float:
        """Mid-price as implied probability (0.0 to 1.0)."""
        return self.mid_price_cents / 100.0


class Event(BaseModel):
    """A Kalshi event containing one or more markets."""

    event_ticker: str
    series_ticker: str = ""
    title: str = ""
    category: str = ""
    sub_title: str = ""
    markets: list[Market] = Field(default_factory=list)
    mutually_exclusive: bool = False


class OrderbookLevel(BaseModel):
    """A single price level in the orderbook."""

    price: int  # cents
    quantity: int


class Orderbook(BaseModel):
    """Full orderbook for a market."""

    market_ticker: str
    yes: list[list[int]] = Field(default_factory=list)  # [[price, quantity], ...]
    no: list[list[int]] = Field(default_factory=list)

    @property
    def best_yes_bid(self) -> int | None:
        """Highest yes bid price in cents."""
        if self.yes:
            return max(level[0] for level in self.yes)
        return None

    @property
    def best_no_bid(self) -> int | None:
        """Highest no bid price in cents."""
        if self.no:
            return max(level[0] for level in self.no)
        return None

    @property
    def best_yes_ask(self) -> int | None:
        """Best yes ask = 100 - best_no_bid (binary market reciprocal)."""
        if self.best_no_bid is not None:
            return 100 - self.best_no_bid
        return None

    def depth_at_price(self, side: OrderSide, min_price: int) -> int:
        """Total quantity available at or better than given price."""
        levels = self.yes if side == OrderSide.YES else self.no
        return sum(qty for price, qty in levels if price >= min_price)


class Position(BaseModel):
    """A portfolio position."""

    ticker: str
    market_exposure: int = 0  # cents
    resting_orders_count: int = 0
    total_traded: int = 0
    realized_pnl: int = 0  # cents


class Balance(BaseModel):
    """Account balance information. All values in cents."""

    balance: int = 0  # available balance
    portfolio_value: int = 0


class Order(BaseModel):
    """An order on the exchange."""

    order_id: str = ""
    ticker: str = ""
    side: OrderSide = OrderSide.YES
    action: OrderAction = OrderAction.BUY
    status: str = ""
    type: str = ""
    yes_price: int | None = None  # cents
    no_price: int | None = None  # cents
    count: int = 0
    remaining_count: int = 0
    taker_fees: int = 0  # cents
    maker_fees: int = 0  # cents
    created_time: datetime | None = None
    expiration_time: datetime | None = None
    time_in_force: TimeInForce = TimeInForce.GOOD_TILL_CANCELED


class Trade(BaseModel):
    """A historical trade."""

    trade_id: str = ""
    ticker: str = ""
    side: OrderSide = OrderSide.YES
    yes_price: int = 0  # cents
    no_price: int = 0  # cents
    count: int = 0
    created_time: datetime | None = None
    taker_side: str = ""


class Candlestick(BaseModel):
    """A candlestick data point."""

    ticker: str = ""
    period_start: datetime | None = None
    open: int = 0  # cents
    high: int = 0  # cents
    low: int = 0  # cents
    close: int = 0  # cents
    volume: int = 0
    open_interest: int = 0


class MarketsResponse(BaseModel):
    """Paginated response for markets list."""

    cursor: str | None = None
    markets: list[Market] = Field(default_factory=list)


class EventsResponse(BaseModel):
    """Paginated response for events list."""

    cursor: str | None = None
    events: list[Event] = Field(default_factory=list)


class TradesResponse(BaseModel):
    """Paginated response for trades list."""

    cursor: str | None = None
    trades: list[Trade] = Field(default_factory=list)
