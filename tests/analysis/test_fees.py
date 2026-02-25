"""Tests for fee calculator."""

from kalshi_intel.analysis.fees import (
    breakeven_edge,
    maker_fee_cents,
    net_payout_cents,
    taker_fee_cents,
)


class TestTakerFee:
    def test_single_contract_at_50c(self):
        # ceil(0.07 * 1 * 0.5 * 0.5) = ceil(0.0175) = 1
        assert taker_fee_cents(1, 50) == 1

    def test_ten_contracts_at_50c(self):
        # ceil(0.07 * 10 * 0.5 * 0.5) = ceil(0.175) = 1
        assert taker_fee_cents(10, 50) == 1

    def test_hundred_contracts_at_50c(self):
        # ceil(0.07 * 100 * 0.5 * 0.5) = ceil(1.75) = 2
        assert taker_fee_cents(100, 50) == 2

    def test_at_extreme_price_low(self):
        # ceil(0.07 * 1 * 0.05 * 0.95) = ceil(0.003325) = 1
        assert taker_fee_cents(1, 5) == 1

    def test_at_extreme_price_high(self):
        # ceil(0.07 * 1 * 0.95 * 0.05) = ceil(0.003325) = 1
        assert taker_fee_cents(1, 95) == 1

    def test_zero_count_returns_zero(self):
        assert taker_fee_cents(0, 50) == 0

    def test_invalid_price_returns_zero(self):
        assert taker_fee_cents(1, 0) == 0
        assert taker_fee_cents(1, 100) == 0
        assert taker_fee_cents(1, -5) == 0

    def test_fee_symmetric(self):
        """Fee at price P equals fee at price (100-P)."""
        assert taker_fee_cents(10, 30) == taker_fee_cents(10, 70)
        assert taker_fee_cents(10, 20) == taker_fee_cents(10, 80)

    def test_sp500_halved(self):
        regular = taker_fee_cents(100, 50, sp500=False)
        sp500 = taker_fee_cents(100, 50, sp500=True)
        assert sp500 <= regular


class TestMakerFee:
    def test_maker_always_less_than_taker(self):
        for price in range(1, 100):
            for count in [1, 10, 100]:
                maker = maker_fee_cents(count, price)
                taker = taker_fee_cents(count, price)
                assert maker <= taker, f"Maker > taker at price={price}, count={count}"

    def test_single_contract_at_50c(self):
        # ceil(0.0175 * 1 * 0.5 * 0.5) = ceil(0.004375) = 1
        assert maker_fee_cents(1, 50) == 1


class TestBreakevenEdge:
    def test_lower_at_50c_than_extremes(self):
        """At extreme prices the payout is small, so breakeven edge is higher."""
        edge_50 = breakeven_edge(50)
        edge_90 = breakeven_edge(90)
        assert edge_50 < edge_90

    def test_maker_lower_than_taker(self):
        assert breakeven_edge(50, is_maker=True) < breakeven_edge(50, is_maker=False)

    def test_positive_for_valid_prices(self):
        for price in range(1, 100):
            assert breakeven_edge(price) > 0


class TestNetPayout:
    def test_yes_wins_at_50c(self):
        pnl = net_payout_cents("yes", 50, 1, result="yes")
        # Payout 100 - cost 50 - fee
        assert pnl > 0

    def test_yes_loses_at_50c(self):
        pnl = net_payout_cents("yes", 50, 1, result="no")
        # Payout 0 - cost 50 - fee
        assert pnl < 0

    def test_no_result_returns_negative_cost(self):
        pnl = net_payout_cents("yes", 50, 1, result=None)
        assert pnl < 0  # Just the cost basis
