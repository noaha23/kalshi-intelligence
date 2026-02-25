"""Multi-factor scoring rubric for evaluating contract opportunities."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from kalshi_intel.client.models import Market, Orderbook

# Categories with known public data sources
CATEGORY_DATA_SOURCES: dict[str, list[str]] = {
    "economics": ["BLS (CPI, Jobs)", "FRED", "Atlanta Fed GDPNow", "CME FedWatch"],
    "weather": ["NOAA/NWS", "Weather Underground", "ECMWF", "GFS models"],
    "politics": ["FiveThirtyEight", "RealClearPolitics", "The Economist", "Polling aggregators"],
    "financials": ["Yahoo Finance", "Bloomberg", "CME Group", "CBOE VIX"],
    "crypto": ["CoinGecko", "Binance API", "Glassnode", "Funding rates"],
    "transportation": ["TSA checkpoint data (daily)", "DOT statistics"],
    "sports": ["ESPN", "The Odds API", "team stats databases"],
}


@dataclass
class ScoringWeights:
    """Configurable weights for multi-factor scoring."""

    liquidity: float = 0.25
    mispricing_potential: float = 0.25
    data_availability: float = 0.20
    time_to_resolution: float = 0.15
    hedgeability: float = 0.15


@dataclass
class MarketScore:
    """Scored market with breakdown."""

    market: Market
    total_score: float  # 0.0 to 1.0
    liquidity_score: float
    mispricing_score: float
    data_score: float
    time_score: float
    hedge_score: float
    notes: list[str] = field(default_factory=list)


def score_liquidity(market: Market, orderbook: Orderbook | None = None) -> float:
    """Score 0-1 based on volume, open interest, and spread.

    Thresholds:
    - 24h volume: 100+ = 0.5, 500+ = 0.75, 1000+ = 1.0
    - Open interest: 50+ = 0.5, 200+ = 0.75, 500+ = 1.0
    - Spread: < 3c = 1.0, < 5c = 0.75, < 10c = 0.5, >= 15c = 0.25
    """
    # Volume score
    vol = market.volume_24h
    if vol >= 1000:
        vol_score = 1.0
    elif vol >= 500:
        vol_score = 0.75
    elif vol >= 100:
        vol_score = 0.5
    elif vol >= 25:
        vol_score = 0.25
    else:
        vol_score = 0.1

    # Open interest score
    oi = market.open_interest
    if oi >= 500:
        oi_score = 1.0
    elif oi >= 200:
        oi_score = 0.75
    elif oi >= 50:
        oi_score = 0.5
    elif oi >= 10:
        oi_score = 0.25
    else:
        oi_score = 0.1

    # Spread score
    spread = market.spread_cents
    if spread <= 3:
        spread_score = 1.0
    elif spread <= 5:
        spread_score = 0.75
    elif spread <= 10:
        spread_score = 0.5
    elif spread <= 15:
        spread_score = 0.25
    else:
        spread_score = 0.1

    # Depth score from orderbook
    depth_score = 0.5  # default if no orderbook
    if orderbook:
        total_depth = 0
        for level in orderbook.yes:
            total_depth += level[1] if len(level) > 1 else 0
        for level in orderbook.no:
            total_depth += level[1] if len(level) > 1 else 0
        if total_depth >= 500:
            depth_score = 1.0
        elif total_depth >= 200:
            depth_score = 0.75
        elif total_depth >= 50:
            depth_score = 0.5
        else:
            depth_score = 0.25

    return vol_score * 0.3 + oi_score * 0.3 + spread_score * 0.25 + depth_score * 0.15


def score_mispricing_potential(market: Market) -> float:
    """Score 0-1 based on price range.

    Contracts in the 30-70c range have the highest potential for
    finding edge -- enough uncertainty for mispricing but not so extreme
    that fees eat all profit.

    50c = max score (maximum information asymmetry potential).
    < 10c or > 90c = low score (hard to find edge, fee drag).
    """
    mid = market.mid_price_cents
    if mid <= 0 or mid >= 100:
        return 0.0

    # Peak at 50, symmetric falloff
    # Score = 1 - (|mid - 50| / 50)^2
    distance = abs(mid - 50) / 50.0
    score = 1.0 - (distance**1.5)
    return max(0.0, min(1.0, score))


def score_data_availability(market: Market) -> float:
    """Score 0-1 based on whether public data sources exist for this market.

    Uses category matching and keyword detection in rules.
    """
    score = 0.3  # base score (some data is always available)

    # Check category
    category = market.category.lower() if market.category else ""
    for cat_key, sources in CATEGORY_DATA_SOURCES.items():
        if cat_key in category:
            score = 0.5 + 0.1 * min(len(sources), 5)
            break

    # Check rules for data-rich keywords
    rules = (market.rules_primary + " " + market.rules_secondary).lower()
    data_keywords = [
        "cpi",
        "inflation",
        "unemployment",
        "gdp",
        "fed",
        "fomc",
        "temperature",
        "weather",
        "forecast",
        "noaa",
        "s&p",
        "nasdaq",
        "dow",
        "bitcoin",
        "btc",
        "eth",
        "tsa",
        "passenger",
        "poll",
        "election",
        "approval rating",
        "earnings",
        "revenue",
    ]
    matches = sum(1 for kw in data_keywords if kw in rules)
    if matches > 0:
        score = min(1.0, score + 0.1 * matches)

    return min(1.0, score)


def score_time_to_resolution(market: Market) -> float:
    """Score 0-1 based on days until close.

    Sweet spot: 7-30 days (enough time to research but not too far out).
    < 2 days: too little time to act
    > 90 days: too uncertain, capital locked up
    """
    if market.close_time is None:
        return 0.3

    now = datetime.now(UTC)
    close = market.close_time
    if close.tzinfo is None:
        close = close.replace(tzinfo=UTC)
    days = (close - now).days

    if days <= 0:
        return 0.0
    elif days <= 2:
        return 0.3
    elif days <= 7:
        return 0.7
    elif days <= 14:
        return 1.0
    elif days <= 30:
        return 0.9
    elif days <= 60:
        return 0.6
    elif days <= 90:
        return 0.4
    else:
        return 0.2


def score_hedgeability(market: Market, related_markets: list[Market] | None = None) -> float:
    """Score 0-1 based on hedging potential.

    Higher score if there are related markets in the same event
    that can serve as natural hedges.
    """
    if not related_markets:
        return 0.3  # standalone market, limited hedging

    # More related markets = better hedging options
    n = len(related_markets)
    if n >= 5:
        return 1.0
    elif n >= 3:
        return 0.8
    elif n >= 1:
        return 0.6
    return 0.3


def score_market(
    market: Market,
    orderbook: Orderbook | None = None,
    related_markets: list[Market] | None = None,
    weights: ScoringWeights | None = None,
) -> MarketScore:
    """Compute composite score for a market."""
    w = weights or ScoringWeights()

    liq = score_liquidity(market, orderbook)
    mis = score_mispricing_potential(market)
    data = score_data_availability(market)
    time_ = score_time_to_resolution(market)
    hedge = score_hedgeability(market, related_markets)

    total = (
        w.liquidity * liq
        + w.mispricing_potential * mis
        + w.data_availability * data
        + w.time_to_resolution * time_
        + w.hedgeability * hedge
    )

    notes = []
    if liq < 0.3:
        notes.append("Low liquidity -- position entry/exit may be difficult")
    if mis > 0.8:
        notes.append("Price near 50c -- high mispricing potential zone")
    if data > 0.7:
        notes.append("Strong public data sources available")
    if time_ < 0.3:
        notes.append("Very short or very long time to resolution")

    return MarketScore(
        market=market,
        total_score=total,
        liquidity_score=liq,
        mispricing_score=mis,
        data_score=data,
        time_score=time_,
        hedge_score=hedge,
        notes=notes,
    )
