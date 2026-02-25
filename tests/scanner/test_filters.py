"""Tests for market filters."""

from kalshi_intel.scanner.filters import (
    MinOpenInterestFilter,
    MinVolumeFilter,
    PriceRangeFilter,
    SpreadFilter,
    StatusFilter,
    apply_filters,
    default_filters,
)


class TestStatusFilter:
    def test_active_passes(self, sample_market):
        f = StatusFilter(allowed_statuses=["active"])
        assert f.passes(sample_market) is True

    def test_wrong_status_fails(self, sample_market):
        f = StatusFilter(allowed_statuses=["closed"])
        assert f.passes(sample_market) is False


class TestMinVolumeFilter:
    def test_above_threshold_passes(self, sample_market):
        f = MinVolumeFilter(min_volume_24h=100)
        assert f.passes(sample_market) is True  # volume_24h=150

    def test_below_threshold_fails(self, sample_market):
        f = MinVolumeFilter(min_volume_24h=200)
        assert f.passes(sample_market) is False


class TestMinOpenInterestFilter:
    def test_above_threshold_passes(self, sample_market):
        f = MinOpenInterestFilter(min_oi=100)
        assert f.passes(sample_market) is True  # OI=200

    def test_below_threshold_fails(self, sample_market):
        f = MinOpenInterestFilter(min_oi=500)
        assert f.passes(sample_market) is False


class TestSpreadFilter:
    def test_narrow_spread_passes(self, sample_market):
        f = SpreadFilter(max_spread_cents=10)
        assert f.passes(sample_market) is True  # spread=4c

    def test_wide_spread_fails(self, sample_market):
        f = SpreadFilter(max_spread_cents=2)
        assert f.passes(sample_market) is False


class TestPriceRangeFilter:
    def test_mid_price_passes(self, sample_market):
        f = PriceRangeFilter(min_price=10, max_price=90)
        assert f.passes(sample_market) is True

    def test_extreme_price_fails(self, sample_market):
        sample_market.yes_bid = 2
        sample_market.yes_ask = 4
        sample_market.last_price = 3
        f = PriceRangeFilter(min_price=10, max_price=90)
        assert f.passes(sample_market) is False


class TestApplyFilters:
    def test_filters_chain(self, sample_market, low_liquidity_market):
        markets = [sample_market, low_liquidity_market]
        filters = [MinVolumeFilter(min_volume_24h=100)]
        result = apply_filters(markets, filters)
        assert len(result) == 1
        assert result[0].ticker == sample_market.ticker


class TestDefaultFilters:
    def test_returns_filters(self):
        filters = default_filters()
        assert len(filters) > 0
