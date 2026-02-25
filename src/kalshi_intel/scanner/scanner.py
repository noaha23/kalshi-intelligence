"""Daily market scanning workflow orchestrator."""

import contextlib
import logging

from kalshi_intel.client.models import Market
from kalshi_intel.client.rest import KalshiRestClient
from kalshi_intel.scanner.filters import MarketFilter, apply_filters, default_filters
from kalshi_intel.scanner.scoring import MarketScore, ScoringWeights, score_market

logger = logging.getLogger(__name__)


class DailyScanner:
    """Orchestrates the daily market scanning workflow.

    1. Fetch all active markets
    2. Apply filters (min volume, category, etc.)
    3. Fetch orderbooks for filtered markets
    4. Score each market
    5. Rank and return top N opportunities
    """

    def __init__(
        self,
        client: KalshiRestClient,
        filters: list[MarketFilter] | None = None,
        weights: ScoringWeights | None = None,
        top_n: int = 20,
    ) -> None:
        self.client = client
        self.filters = filters or default_filters()
        self.weights = weights or ScoringWeights()
        self.top_n = top_n

    def run(self) -> list[MarketScore]:
        """Execute full scan. Returns scored markets sorted descending by score."""
        logger.info("Starting daily scan...")

        # 1. Fetch all active markets
        all_markets = self.client.get_all_markets(status="active")
        logger.info(f"Fetched {len(all_markets)} active markets")

        # 2. Apply filters
        filtered = apply_filters(all_markets, self.filters)
        logger.info(f"{len(filtered)} markets pass filters (from {len(all_markets)})")

        if not filtered:
            return []

        # 3. Group by event for hedgeability scoring
        event_groups: dict[str, list[Market]] = {}
        for m in filtered:
            event_groups.setdefault(m.event_ticker, []).append(m)

        # 4. Score each market (fetch orderbooks for top candidates)
        scored: list[MarketScore] = []
        for market in filtered:
            related = [
                m for m in event_groups.get(market.event_ticker, []) if m.ticker != market.ticker
            ]

            # Try to fetch orderbook (skip on failure)
            orderbook = None
            try:
                orderbook = self.client.get_orderbook(market.ticker)
            except Exception as e:
                logger.debug(f"Could not fetch orderbook for {market.ticker}: {e}")

            score = score_market(
                market,
                orderbook=orderbook,
                related_markets=related,
                weights=self.weights,
            )
            scored.append(score)

        # 5. Sort by total score descending
        scored.sort(key=lambda s: s.total_score, reverse=True)

        top = scored[: self.top_n]
        logger.info(f"Top {len(top)} opportunities identified")
        return top

    def scan_event(self, event_ticker: str) -> list[MarketScore]:
        """Scan all markets within a specific event."""
        event = self.client.get_event(event_ticker)
        markets = event.markets
        if not markets:
            markets = self.client.get_all_markets(event_ticker=event_ticker)

        scored = []
        for market in markets:
            related = [m for m in markets if m.ticker != market.ticker]
            orderbook = None
            with contextlib.suppress(Exception):
                orderbook = self.client.get_orderbook(market.ticker)

            score = score_market(
                market, orderbook=orderbook, related_markets=related, weights=self.weights
            )
            scored.append(score)

        scored.sort(key=lambda s: s.total_score, reverse=True)
        return scored
