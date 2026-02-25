"""Tests for Kelly criterion position sizing."""

from kalshi_intel.analysis.position_sizing import (
    calculate_position_size,
    fractional_kelly,
    kelly_fraction_binary,
    multi_position_kelly,
)


class TestKellyFraction:
    def test_no_edge_returns_zero(self):
        """When true prob equals market price, no edge, kelly = 0."""
        assert kelly_fraction_binary(0.5, 50) == 0.0

    def test_positive_edge_yes(self):
        """True prob > market price -> positive kelly (bet YES)."""
        frac = kelly_fraction_binary(0.7, 50)
        assert frac > 0

    def test_negative_edge_no(self):
        """True prob < market price -> negative kelly (bet NO)."""
        frac = kelly_fraction_binary(0.3, 50)
        assert frac < 0

    def test_extreme_edge(self):
        """High confidence at low price -> large fraction."""
        frac = kelly_fraction_binary(0.9, 30)
        assert frac > 0.5

    def test_invalid_inputs_return_zero(self):
        assert kelly_fraction_binary(0.0, 50) == 0.0
        assert kelly_fraction_binary(1.0, 50) == 0.0
        assert kelly_fraction_binary(0.5, 0) == 0.0
        assert kelly_fraction_binary(0.5, 100) == 0.0


class TestFractionalKelly:
    def test_quarter_kelly(self):
        full = kelly_fraction_binary(0.7, 50)
        quarter = fractional_kelly(0.7, 50, 0.25)
        assert abs(quarter - full * 0.25) < 1e-10

    def test_half_kelly(self):
        full = kelly_fraction_binary(0.7, 50)
        half = fractional_kelly(0.7, 50, 0.5)
        assert abs(half - full * 0.5) < 1e-10


class TestCalculatePositionSize:
    def test_basic_yes_bet(self):
        result = calculate_position_size(
            true_probability=0.7,
            market_price_cents=50,
            bankroll_cents=100_000,
        )
        assert result.side == "yes"
        assert result.recommended_contracts > 0
        assert result.edge_pct > 0
        assert result.max_cost_cents > 0

    def test_basic_no_bet(self):
        result = calculate_position_size(
            true_probability=0.3,
            market_price_cents=50,
            bankroll_cents=100_000,
        )
        assert result.side == "no"
        assert result.recommended_contracts > 0
        assert result.edge_pct > 0

    def test_no_edge_zero_contracts(self):
        result = calculate_position_size(
            true_probability=0.5,
            market_price_cents=50,
            bankroll_cents=100_000,
        )
        assert result.recommended_contracts == 0

    def test_respects_max_position(self):
        result = calculate_position_size(
            true_probability=0.95,
            market_price_cents=50,
            bankroll_cents=100_000,
            max_position_pct=0.05,
        )
        assert result.max_cost_cents <= 100_000 * 0.05

    def test_higher_kelly_mult_more_contracts(self):
        small = calculate_position_size(0.7, 50, 100_000, kelly_multiplier=0.1)
        large = calculate_position_size(0.7, 50, 100_000, kelly_multiplier=0.5)
        assert large.recommended_contracts >= small.recommended_contracts


class TestMultiPositionKelly:
    def test_total_exposure_capped(self):
        positions = [(0.7, 50), (0.8, 40), (0.6, 60)]
        results = multi_position_kelly(positions, 100_000, max_total_exposure_pct=0.10)
        total_frac = sum(r.adjusted_fraction for r in results)
        assert total_frac <= 0.10 + 1e-6  # small float tolerance
