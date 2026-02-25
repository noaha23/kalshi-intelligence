"""Table and output formatting utilities."""

from rich.table import Table

from kalshi_intel.analysis.position_sizing import PositionSizeResult
from kalshi_intel.scanner.scoring import MarketScore
from kalshi_intel.utils.money import format_cents, format_dollars


def market_scores_table(scores: list[MarketScore]) -> Table:
    """Format scored markets as a Rich table."""
    table = Table(title="Market Opportunities", show_lines=True)
    table.add_column("Rank", style="bold", width=4)
    table.add_column("Ticker", style="cyan", width=30)
    table.add_column("Score", style="bold green", width=6)
    table.add_column("Price", width=6)
    table.add_column("Vol 24h", width=8)
    table.add_column("OI", width=6)
    table.add_column("Spread", width=6)
    table.add_column("Liq", width=5)
    table.add_column("Mis", width=5)
    table.add_column("Data", width=5)
    table.add_column("Time", width=5)

    for i, s in enumerate(scores, 1):
        m = s.market
        table.add_row(
            str(i),
            m.ticker,
            f"{s.total_score:.2f}",
            format_cents(int(m.mid_price_cents)),
            str(m.volume_24h),
            str(m.open_interest),
            format_cents(m.spread_cents),
            f"{s.liquidity_score:.2f}",
            f"{s.mispricing_score:.2f}",
            f"{s.data_score:.2f}",
            f"{s.time_score:.2f}",
        )

    return table


def fee_table(price_cents: int, count: int) -> Table:
    """Format fee calculations as a Rich table."""
    from kalshi_intel.analysis.fees import (
        breakeven_edge,
        maker_fee_cents,
        net_payout_cents,
        taker_fee_cents,
    )

    table = Table(title=f"Fee Analysis: {count} contracts @ {format_cents(price_cents)}")
    table.add_column("Metric", style="bold")
    table.add_column("Taker", style="red")
    table.add_column("Maker", style="green")

    taker = taker_fee_cents(count, price_cents)
    maker = maker_fee_cents(count, price_cents)

    table.add_row("Fee", format_dollars(taker), format_dollars(maker))
    table.add_row(
        "Fee per contract",
        f"{taker / count:.2f}c" if count > 0 else "N/A",
        f"{maker / count:.2f}c" if count > 0 else "N/A",
    )
    table.add_row(
        "Cost (price + fee)",
        format_dollars(price_cents * count + taker),
        format_dollars(price_cents * count + maker),
    )
    table.add_row(
        "Breakeven edge",
        f"{breakeven_edge(price_cents, False):.2%}",
        f"{breakeven_edge(price_cents, True):.2%}",
    )
    table.add_row(
        "P&L if YES wins",
        format_dollars(net_payout_cents("yes", price_cents, count, "yes", False)),
        format_dollars(net_payout_cents("yes", price_cents, count, "yes", True)),
    )
    table.add_row(
        "P&L if NO wins",
        format_dollars(net_payout_cents("yes", price_cents, count, "no", False)),
        format_dollars(net_payout_cents("yes", price_cents, count, "no", True)),
    )

    return table


def position_size_table(result: PositionSizeResult) -> Table:
    """Format position sizing result as a Rich table."""
    table = Table(title="Position Sizing (Kelly Criterion)")
    table.add_column("Metric", style="bold")
    table.add_column("Value")

    table.add_row("Recommended side", result.side.upper())
    table.add_row("True probability", f"{result.true_probability:.1%}")
    table.add_row("Market price", format_cents(result.price_cents))
    table.add_row("Edge", f"{result.edge_pct:.2%}")
    table.add_row("Raw Kelly fraction", f"{result.kelly_fraction:.4f}")
    table.add_row("Adjusted fraction", f"{result.adjusted_fraction:.4f}")
    table.add_row("Contracts", str(result.recommended_contracts))
    table.add_row("Total cost", format_dollars(result.max_cost_cents))
    table.add_row("Expected value", format_dollars(int(result.expected_value_cents)))

    return table
