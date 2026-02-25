"""Daily market scan report generation."""

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from kalshi_intel.analysis.probability import ProbabilityEstimate
from kalshi_intel.scanner.scoring import MarketScore
from kalshi_intel.utils.money import format_cents


@dataclass
class DailyReport:
    """Structured daily scan report."""

    date: date
    markets_scanned: int
    markets_after_filter: int
    top_opportunities: list[MarketScore]
    ai_estimates: list[ProbabilityEstimate] | None = None
    generated_at: str = ""

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now(UTC).isoformat()


class DailyReportGenerator:
    """Generates daily market scan reports in Markdown and JSON."""

    def __init__(self, output_dir: Path = Path("data/reports")) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        scored_markets: list[MarketScore],
        total_scanned: int = 0,
        total_filtered: int = 0,
        ai_estimates: list[ProbabilityEstimate] | None = None,
    ) -> DailyReport:
        """Build the report data structure."""
        return DailyReport(
            date=date.today(),
            markets_scanned=total_scanned,
            markets_after_filter=total_filtered,
            top_opportunities=scored_markets,
            ai_estimates=ai_estimates,
        )

    def to_markdown(self, report: DailyReport) -> str:
        """Render report as Markdown."""
        lines = [
            f"# Daily Market Scan Report - {report.date}",
            "",
            f"*Generated: {report.generated_at}*",
            "",
            "## Summary",
            "",
            f"- Markets scanned: {report.markets_scanned}",
            f"- After filters: {report.markets_after_filter}",
            f"- Top opportunities: {len(report.top_opportunities)}",
            "",
            "## Top Opportunities",
            "",
            "| Rank | Ticker | Score | Price | Vol 24h | OI | Notes |",
            "|------|--------|-------|-------|---------|-----|-------|",
        ]

        for i, s in enumerate(report.top_opportunities, 1):
            m = s.market
            notes = "; ".join(s.notes[:2]) if s.notes else ""
            lines.append(
                f"| {i} | `{m.ticker}` | {s.total_score:.2f} | "
                f"{format_cents(int(m.mid_price_cents))} | {m.volume_24h} | "
                f"{m.open_interest} | {notes} |"
            )

        if report.ai_estimates:
            lines.extend(
                [
                    "",
                    "## AI Probability Estimates",
                    "",
                    "| Ticker | Market Price | AI Estimate | Edge | Confidence |",
                    "|--------|-------------|-------------|------|------------|",
                ]
            )
            for est in report.ai_estimates:
                lines.append(
                    f"| `{est.market_ticker}` | - | "
                    f"{est.estimated_probability:.1%} | "
                    f"{est.edge_vs_market:+.1%} | {est.confidence:.0%} |"
                )

        lines.extend(
            [
                "",
                "---",
                "*DISCLAIMER: This report is for research purposes only. Not financial advice.*",
            ]
        )

        return "\n".join(lines)

    def to_json(self, report: DailyReport) -> str:
        """Render report as JSON."""
        data = {
            "date": report.date.isoformat(),
            "generated_at": report.generated_at,
            "markets_scanned": report.markets_scanned,
            "markets_after_filter": report.markets_after_filter,
            "top_opportunities": [
                {
                    "ticker": s.market.ticker,
                    "total_score": s.total_score,
                    "price_cents": int(s.market.mid_price_cents),
                    "volume_24h": s.market.volume_24h,
                    "open_interest": s.market.open_interest,
                    "scores": {
                        "liquidity": s.liquidity_score,
                        "mispricing": s.mispricing_score,
                        "data": s.data_score,
                        "time": s.time_score,
                        "hedge": s.hedge_score,
                    },
                    "notes": s.notes,
                }
                for s in report.top_opportunities
            ],
        }
        return json.dumps(data, indent=2)

    def save(self, report: DailyReport) -> Path:
        """Write report to output_dir."""
        md_path = self.output_dir / f"{report.date}_daily_report.md"
        md_path.write_text(self.to_markdown(report))

        json_path = self.output_dir / f"{report.date}_daily_report.json"
        json_path.write_text(self.to_json(report))

        return md_path
