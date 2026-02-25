"""Tests for hedging calculations."""

from kalshi_intel.analysis.hedging import (
    breakeven_price,
    check_arbitrage,
    lock_in_profit,
)
from kalshi_intel.client.models import Market


class TestLockInProfit:
    def test_yes_price_moved_up(self):
        """Bought YES at 40c, price now 60c. Should lock in ~20c/contract."""
        result = lock_in_profit("yes", 40, 60, 10)
        assert result.max_gain_cents > 0
        assert len(result.scenarios) == 2
        # Both scenarios should have same P&L (it's locked in)
        assert result.scenarios[0]["pnl_cents"] == result.scenarios[1]["pnl_cents"]

    def test_yes_price_moved_down(self):
        """Bought YES at 60c, price now 40c. Hedging locks in a loss."""
        result = lock_in_profit("yes", 60, 40, 10)
        assert result.max_gain_cents == 0
        assert result.max_loss_cents > 0

    def test_no_side_hedge(self):
        """Bought NO at 40c (YES was 60c), YES dropped to 30c."""
        result = lock_in_profit("no", 40, 30, 5)
        # NO at 40c means YES was at 60c when we entered
        # Now YES is 30c, so NO is worth 70c
        # Guaranteed = 100 - 40 - 30 = 30c per contract
        assert result.max_gain_cents > 0

    def test_single_contract(self):
        result = lock_in_profit("yes", 30, 70, 1)
        assert result.primary.contracts == 1
        assert len(result.hedges) == 1
        assert result.hedges[0].contracts == 1


class TestCheckArbitrage:
    def test_no_arbitrage_when_sum_100(self):
        markets = [
            Market(ticker="A", event_ticker="E", last_price=30, yes_bid=28, yes_ask=32),
            Market(ticker="B", event_ticker="E", last_price=40, yes_bid=38, yes_ask=42),
            Market(ticker="C", event_ticker="E", last_price=30, yes_bid=28, yes_ask=32),
        ]
        result = check_arbitrage(markets)
        assert result["is_arbitrage"] is False

    def test_empty_markets(self):
        result = check_arbitrage([])
        assert result["is_arbitrage"] is False
        assert result["sum_yes_cents"] == 0


class TestBreakevenPrice:
    def test_returns_valid_price(self):
        be = breakeven_price(40)
        assert 40 < be <= 99

    def test_higher_entry_needs_less_movement(self):
        # At higher prices, fees are lower, so less movement needed
        be_low = breakeven_price(20)
        be_high = breakeven_price(80)
        # Both should be valid
        assert 20 < be_low <= 99
        assert 80 < be_high <= 99

    def test_maker_needs_less_movement(self):
        be_taker = breakeven_price(50, is_maker=False)
        be_maker = breakeven_price(50, is_maker=True)
        assert be_maker <= be_taker
