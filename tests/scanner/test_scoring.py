"""Tests for market scoring rubric."""

from kalshi_intel.scanner.scoring import (
    score_data_availability,
    score_liquidity,
    score_market,
    score_mispricing_potential,
    score_time_to_resolution,
)


class TestScoreLiquidity:
    def test_high_liquidity(self, sample_market, sample_orderbook):
        score = score_liquidity(sample_market, sample_orderbook)
        assert 0.0 <= score <= 1.0
        assert score > 0.3  # should be decent with 150 volume, 200 OI

    def test_low_liquidity(self, low_liquidity_market):
        score = score_liquidity(low_liquidity_market)
        assert 0.0 <= score <= 1.0
        assert score < 0.5


class TestScoreMispricingPotential:
    def test_peak_at_50c(self, sample_market):
        score = score_mispricing_potential(sample_market)
        assert score > 0.9  # mid_price ~50c should be near max

    def test_low_at_extremes(self, low_liquidity_market):
        # last_price=40, so still mid-range
        low_liquidity_market.last_price = 5
        low_liquidity_market.yes_bid = 0
        low_liquidity_market.yes_ask = 0
        score = score_mispricing_potential(low_liquidity_market)
        assert score < 0.5


class TestScoreDataAvailability:
    def test_economics_category(self, sample_market):
        score = score_data_availability(sample_market)
        assert score > 0.5  # category=economics + CPI in rules

    def test_unknown_category(self, low_liquidity_market):
        low_liquidity_market.category = "unknown"
        low_liquidity_market.rules_primary = "Something obscure"
        score = score_data_availability(low_liquidity_market)
        assert score <= 0.5


class TestScoreTimeToResolution:
    def test_returns_valid_range(self, sample_market):
        score = score_time_to_resolution(sample_market)
        assert 0.0 <= score <= 1.0


class TestScoreMarket:
    def test_composite_score_in_range(self, sample_market, sample_orderbook):
        result = score_market(sample_market, sample_orderbook)
        assert 0.0 <= result.total_score <= 1.0
        assert result.market == sample_market

    def test_all_subscores_in_range(self, sample_market, sample_orderbook):
        result = score_market(sample_market, sample_orderbook)
        assert 0.0 <= result.liquidity_score <= 1.0
        assert 0.0 <= result.mispricing_score <= 1.0
        assert 0.0 <= result.data_score <= 1.0
        assert 0.0 <= result.time_score <= 1.0
        assert 0.0 <= result.hedge_score <= 1.0
