"""Market filter predicates for daily scanning."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from kalshi_intel.client.models import Market


class MarketFilter(ABC):
    """Base class for market filter predicates."""

    @abstractmethod
    def passes(self, market: Market) -> bool: ...

    @abstractmethod
    def description(self) -> str: ...


class StatusFilter(MarketFilter):
    """Filter by market status."""

    def __init__(self, allowed_statuses: list[str] | None = None) -> None:
        self.allowed = allowed_statuses or ["active"]

    def passes(self, market: Market) -> bool:
        return market.status.value in self.allowed

    def description(self) -> str:
        return f"Status in {self.allowed}"


class MinVolumeFilter(MarketFilter):
    """Require minimum 24h trading volume."""

    def __init__(self, min_volume_24h: int = 100) -> None:
        self.min_volume = min_volume_24h

    def passes(self, market: Market) -> bool:
        return market.volume_24h >= self.min_volume

    def description(self) -> str:
        return f"24h volume >= {self.min_volume}"


class MinOpenInterestFilter(MarketFilter):
    """Require minimum open interest."""

    def __init__(self, min_oi: int = 50) -> None:
        self.min_oi = min_oi

    def passes(self, market: Market) -> bool:
        return market.open_interest >= self.min_oi

    def description(self) -> str:
        return f"Open interest >= {self.min_oi}"


class MaxDaysToCloseFilter(MarketFilter):
    """Reject markets closing too far out."""

    def __init__(self, max_days: int = 90) -> None:
        self.max_days = max_days

    def passes(self, market: Market) -> bool:
        if market.close_time is None:
            return False
        now = datetime.now(UTC)
        close = market.close_time
        if close.tzinfo is None:
            close = close.replace(tzinfo=UTC)
        days = (close - now).days
        return 0 < days <= self.max_days

    def description(self) -> str:
        return f"Closes within {self.max_days} days"


class MinDaysToCloseFilter(MarketFilter):
    """Reject markets closing too soon (not enough time to research)."""

    def __init__(self, min_days: int = 1) -> None:
        self.min_days = min_days

    def passes(self, market: Market) -> bool:
        if market.close_time is None:
            return False
        now = datetime.now(UTC)
        close = market.close_time
        if close.tzinfo is None:
            close = close.replace(tzinfo=UTC)
        days = (close - now).days
        return days >= self.min_days

    def description(self) -> str:
        return f"At least {self.min_days} days until close"


class SpreadFilter(MarketFilter):
    """Reject markets with bid-ask spread wider than threshold."""

    def __init__(self, max_spread_cents: int = 15) -> None:
        self.max_spread = max_spread_cents

    def passes(self, market: Market) -> bool:
        return market.spread_cents <= self.max_spread

    def description(self) -> str:
        return f"Spread <= {self.max_spread}c"


class PriceRangeFilter(MarketFilter):
    """Only include markets in a price range (avoid extreme longshots)."""

    def __init__(self, min_price: int = 5, max_price: int = 95) -> None:
        self.min_price = min_price
        self.max_price = max_price

    def passes(self, market: Market) -> bool:
        mid = market.mid_price_cents
        return self.min_price <= mid <= self.max_price

    def description(self) -> str:
        return f"Price between {self.min_price}c and {self.max_price}c"


def default_filters() -> list[MarketFilter]:
    """Standard filter chain for daily scanning."""
    return [
        StatusFilter(allowed_statuses=["active"]),
        MinVolumeFilter(min_volume_24h=100),
        MinOpenInterestFilter(min_oi=50),
        MinDaysToCloseFilter(min_days=1),
        MaxDaysToCloseFilter(max_days=90),
        SpreadFilter(max_spread_cents=15),
        PriceRangeFilter(min_price=5, max_price=95),
    ]


def apply_filters(markets: list[Market], filters: list[MarketFilter]) -> list[Market]:
    """Apply all filters and return passing markets."""
    result = markets
    for f in filters:
        result = [m for m in result if f.passes(m)]
    return result
