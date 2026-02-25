"""Historical Kalshi market data retrieval and analysis."""

import logging

from kalshi_intel.client.models import Candlestick, Trade
from kalshi_intel.client.rest import KalshiRestClient

logger = logging.getLogger(__name__)


class HistoricalDataManager:
    """Retrieve and analyze historical Kalshi market data.

    Uses the /historical/* and candlestick endpoints.
    """

    def __init__(self, client: KalshiRestClient) -> None:
        self.client = client

    def get_trade_history(self, ticker: str, limit: int = 1000) -> list[Trade]:
        """Fetch recent trades for a market."""
        all_trades: list[Trade] = []
        cursor = None

        while len(all_trades) < limit:
            batch_limit = min(200, limit - len(all_trades))
            resp = self.client.get_trades(ticker=ticker, limit=batch_limit, cursor=cursor)
            all_trades.extend(resp.trades)
            if not resp.cursor or not resp.trades:
                break
            cursor = resp.cursor

        return all_trades

    def get_price_history(
        self,
        series_ticker: str,
        ticker: str,
        period_interval: int = 1440,
    ) -> list[Candlestick]:
        """Fetch candlestick data for a market.

        Args:
            series_ticker: Series the market belongs to.
            ticker: Market ticker.
            period_interval: Candle size in minutes (1, 60, or 1440).
        """
        return self.client.get_candlesticks(
            series_ticker=series_ticker,
            ticker=ticker,
            period_interval=period_interval,
        )

    def calculate_historical_accuracy(
        self,
        markets: list[dict],
    ) -> dict:
        """Analyze market calibration from settled markets.

        For each price bucket (0-10%, 10-20%, ..., 90-100%),
        calculate what fraction actually resolved YES.
        Well-calibrated markets: 70% priced contracts should resolve YES ~70% of the time.

        Args:
            markets: List of settled market dicts with 'last_price' and 'result' fields.

        Returns:
            Calibration report with bucket-level accuracy.
        """
        buckets: dict[str, dict] = {}
        for i in range(0, 100, 10):
            label = f"{i}-{i + 10}%"
            buckets[label] = {"count": 0, "yes_count": 0}

        for m in markets:
            price = m.get("last_price", 0)
            result = m.get("result", "")
            if not result:
                continue

            # Determine bucket
            bucket_idx = min(int(price / 10), 9)
            label = f"{bucket_idx * 10}-{bucket_idx * 10 + 10}%"
            buckets[label]["count"] += 1
            if result == "yes":
                buckets[label]["yes_count"] += 1

        # Calculate actual rates
        calibration = {}
        for label, data in buckets.items():
            actual_rate = data["yes_count"] / data["count"] if data["count"] > 0 else None
            calibration[label] = {
                "count": data["count"],
                "yes_count": data["yes_count"],
                "actual_yes_rate": actual_rate,
            }

        total = sum(d["count"] for d in buckets.values())
        return {
            "total_markets": total,
            "calibration_by_bucket": calibration,
        }
