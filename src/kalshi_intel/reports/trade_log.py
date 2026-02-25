"""Trade logging and P&L tracking via CSV."""

import csv
from dataclasses import dataclass, fields
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class TradeEntry:
    """A logged trade (paper or real)."""

    timestamp: str
    market_ticker: str
    side: str  # "yes" or "no"
    action: str  # "buy" or "sell"
    contracts: int
    price_cents: int
    fee_cents: int
    is_paper: bool = True
    notes: str = ""
    probability_estimate: float | None = None
    kelly_fraction: float | None = None
    result: str | None = None  # "yes", "no", or None if unsettled
    pnl_cents: int | None = None


FIELDNAMES = [f.name for f in fields(TradeEntry)]


class TradeLog:
    """Append-only trade log stored as CSV."""

    def __init__(self, log_path: Path = Path("data/trades/trade_log.csv")) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create file with headers if it doesn't exist
        if not self.log_path.exists():
            with open(self.log_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writeheader()

    def log_trade(self, entry: TradeEntry) -> None:
        """Append a trade to the log file."""
        if not entry.timestamp:
            entry.timestamp = datetime.now(UTC).isoformat()

        with open(self.log_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            row = {f.name: getattr(entry, f.name) for f in fields(entry)}
            writer.writerow(row)

    def get_trades(
        self,
        market_ticker: str | None = None,
    ) -> list[TradeEntry]:
        """Read trades from log, optionally filtered by ticker."""
        if not self.log_path.exists():
            return []

        trades = []
        with open(self.log_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if market_ticker and row.get("market_ticker") != market_ticker:
                    continue
                trades.append(
                    TradeEntry(
                        timestamp=row.get("timestamp", ""),
                        market_ticker=row.get("market_ticker", ""),
                        side=row.get("side", ""),
                        action=row.get("action", ""),
                        contracts=int(row.get("contracts", 0)),
                        price_cents=int(row.get("price_cents", 0)),
                        fee_cents=int(row.get("fee_cents", 0)),
                        is_paper=row.get("is_paper", "True").lower() == "true",
                        notes=row.get("notes", ""),
                        probability_estimate=float(row["probability_estimate"])
                        if row.get("probability_estimate")
                        else None,
                        kelly_fraction=float(row["kelly_fraction"])
                        if row.get("kelly_fraction")
                        else None,
                        result=row.get("result") or None,
                        pnl_cents=int(row["pnl_cents"]) if row.get("pnl_cents") else None,
                    )
                )
        return trades

    def calculate_pnl(self, market_ticker: str | None = None) -> dict:
        """Calculate P&L summary from trade log."""
        trades = self.get_trades(market_ticker)

        total_cost = 0
        total_fees = 0
        total_pnl = 0
        wins = 0
        losses = 0

        for t in trades:
            total_cost += t.price_cents * t.contracts
            total_fees += t.fee_cents
            if t.pnl_cents is not None:
                total_pnl += t.pnl_cents
                if t.pnl_cents > 0:
                    wins += 1
                elif t.pnl_cents < 0:
                    losses += 1

        total_settled = wins + losses
        return {
            "total_trades": len(trades),
            "total_cost_cents": total_cost,
            "total_fees_cents": total_fees,
            "realized_pnl_cents": total_pnl,
            "wins": wins,
            "losses": losses,
            "win_rate": wins / total_settled if total_settled > 0 else 0.0,
        }
