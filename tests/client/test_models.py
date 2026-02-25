"""Tests for Pydantic models."""

from kalshi_intel.client.models import Market, Orderbook, OrderSide


class TestMarket:
    def test_mid_price(self, sample_market):
        assert sample_market.mid_price_cents == 50.0

    def test_spread(self, sample_market):
        assert sample_market.spread_cents == 4  # 52 - 48

    def test_implied_probability(self, sample_market):
        assert sample_market.implied_probability == 0.5

    def test_no_bid_ask_uses_last_price(self):
        m = Market(ticker="TEST", event_ticker="EVT", last_price=65)
        assert m.mid_price_cents == 65.0

    def test_zero_spread_when_no_quotes(self):
        m = Market(ticker="TEST", event_ticker="EVT")
        assert m.spread_cents == 0


class TestOrderbook:
    def test_best_yes_bid(self, sample_orderbook):
        assert sample_orderbook.best_yes_bid == 48

    def test_best_no_bid(self, sample_orderbook):
        assert sample_orderbook.best_no_bid == 48

    def test_best_yes_ask(self, sample_orderbook):
        # 100 - best_no_bid = 100 - 48 = 52
        assert sample_orderbook.best_yes_ask == 52

    def test_depth_at_price(self, sample_orderbook):
        depth = sample_orderbook.depth_at_price(OrderSide.YES, 47)
        # Levels at 48 (100) and 47 (200) = 300
        assert depth == 300

    def test_empty_orderbook(self):
        ob = Orderbook(market_ticker="EMPTY")
        assert ob.best_yes_bid is None
        assert ob.best_no_bid is None
        assert ob.best_yes_ask is None
