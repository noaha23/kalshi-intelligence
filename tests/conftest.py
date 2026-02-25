"""Shared test fixtures."""

from datetime import UTC, datetime

import pytest

from kalshi_intel.client.models import Market, MarketStatus, Orderbook


@pytest.fixture
def sample_market() -> Market:
    """A market with known values for deterministic testing."""
    return Market(
        ticker="TEST-MARKET-YES50",
        event_ticker="TEST-EVENT",
        market_type="binary",
        status=MarketStatus.ACTIVE,
        yes_bid=48,
        yes_ask=52,
        no_bid=48,
        no_ask=52,
        last_price=50,
        volume=500,
        volume_24h=150,
        open_interest=200,
        rules_primary="Will the CPI inflation rate exceed 3.0% in March 2025?",
        category="economics",
        close_time=datetime(2025, 4, 1, tzinfo=UTC),
    )


@pytest.fixture
def low_liquidity_market() -> Market:
    """A market with low liquidity."""
    return Market(
        ticker="TEST-LOW-LIQ",
        event_ticker="TEST-EVENT-2",
        market_type="binary",
        status=MarketStatus.ACTIVE,
        yes_bid=30,
        yes_ask=50,
        last_price=40,
        volume=10,
        volume_24h=5,
        open_interest=8,
        rules_primary="Will X happen?",
        close_time=datetime(2025, 5, 1, tzinfo=UTC),
    )


@pytest.fixture
def sample_orderbook() -> Orderbook:
    """An orderbook with known levels."""
    return Orderbook(
        market_ticker="TEST-MARKET-YES50",
        yes=[[48, 100], [47, 200], [46, 300]],
        no=[[48, 150], [47, 250], [46, 350]],
    )
