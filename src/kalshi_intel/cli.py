"""CLI entry point for Kalshi Market Intelligence System."""

import asyncio

import typer
from rich.console import Console

from kalshi_intel import DISCLAIMER

app = typer.Typer(
    name="kalshi-intel",
    help="Kalshi Market Intelligence System -- Research & Analysis Tools",
    no_args_is_help=True,
)
console = Console()


def _get_client():
    """Create and return a configured REST client."""
    from kalshi_intel.client.auth import KalshiAuthenticator
    from kalshi_intel.client.rest import KalshiRestClient
    from kalshi_intel.config import get_settings

    settings = get_settings()
    if not settings.api_key_id:
        console.print("[red]Error: KALSHI_API_KEY_ID not set in .env[/red]")
        raise typer.Exit(1)

    auth = KalshiAuthenticator(settings.api_key_id, settings.private_key_path)
    return KalshiRestClient(
        base_url=settings.base_url,
        authenticator=auth,
        read_rate_limit=settings.read_rate_limit,
        write_rate_limit=settings.write_rate_limit,
    )


def _print_disclaimer():
    console.print(f"\n[dim]{DISCLAIMER}[/dim]\n")


# --- Scan commands ---


@app.command()
def scan(
    top_n: int = typer.Option(20, help="Number of top opportunities to show"),
    category: str | None = typer.Option(None, help="Filter by category"),
    min_volume: int = typer.Option(100, help="Minimum 24h volume"),
    save: bool = typer.Option(False, help="Save report to data/reports/"),
) -> None:
    """Run daily market scan and display top opportunities."""
    from kalshi_intel.reports.formatters import market_scores_table
    from kalshi_intel.scanner.filters import MinVolumeFilter, default_filters
    from kalshi_intel.scanner.scanner import DailyScanner

    client = _get_client()
    filters = default_filters()

    # Override volume filter if specified
    filters = [f for f in filters if not isinstance(f, MinVolumeFilter)]
    filters.append(MinVolumeFilter(min_volume_24h=min_volume))

    scanner = DailyScanner(client=client, filters=filters, top_n=top_n)

    with console.status("Scanning markets..."):
        results = scanner.run()

    if not results:
        console.print("[yellow]No opportunities found matching criteria.[/yellow]")
        return

    table = market_scores_table(results)
    console.print(table)

    if save:
        from kalshi_intel.reports.daily_report import DailyReportGenerator

        gen = DailyReportGenerator()
        report = gen.generate(results)
        path = gen.save(report)
        console.print(f"\nReport saved to {path}")

    _print_disclaimer()


@app.command()
def scan_event(
    event_ticker: str = typer.Argument(..., help="Event ticker to scan"),
) -> None:
    """Scan all markets within a specific event."""
    from kalshi_intel.reports.formatters import market_scores_table
    from kalshi_intel.scanner.scanner import DailyScanner

    client = _get_client()
    scanner = DailyScanner(client=client)

    with console.status(f"Scanning event {event_ticker}..."):
        results = scanner.scan_event(event_ticker)

    if not results:
        console.print("[yellow]No markets found for this event.[/yellow]")
        return

    table = market_scores_table(results)
    console.print(table)
    _print_disclaimer()


# --- Analysis commands ---


@app.command()
def fees(
    price: int = typer.Argument(..., help="Contract price in cents (1-99)"),
    count: int = typer.Option(1, help="Number of contracts"),
) -> None:
    """Calculate taker and maker fees for a trade."""
    from kalshi_intel.reports.formatters import fee_table

    if not 1 <= price <= 99:
        console.print("[red]Price must be between 1 and 99 cents.[/red]")
        raise typer.Exit(1)

    table = fee_table(price, count)
    console.print(table)


@app.command()
def position_size(
    true_prob: float = typer.Argument(..., help="Your estimated true probability (0-1)"),
    market_price: int = typer.Argument(..., help="Current market price in cents"),
    bankroll: int = typer.Option(100_000, help="Bankroll in cents"),
    kelly_mult: float = typer.Option(0.25, help="Kelly fraction multiplier"),
    max_pct: float = typer.Option(0.05, help="Max position as fraction of bankroll"),
) -> None:
    """Calculate recommended position size using Kelly criterion."""
    from kalshi_intel.analysis.position_sizing import calculate_position_size
    from kalshi_intel.reports.formatters import position_size_table

    if not 0 < true_prob < 1:
        console.print("[red]Probability must be between 0 and 1.[/red]")
        raise typer.Exit(1)
    if not 1 <= market_price <= 99:
        console.print("[red]Market price must be between 1 and 99 cents.[/red]")
        raise typer.Exit(1)

    result = calculate_position_size(
        true_probability=true_prob,
        market_price_cents=market_price,
        bankroll_cents=bankroll,
        kelly_multiplier=kelly_mult,
        max_position_pct=max_pct,
    )

    table = position_size_table(result)
    console.print(table)
    _print_disclaimer()


@app.command()
def estimate(
    ticker: str = typer.Argument(..., help="Market ticker"),
    provider: str = typer.Option("anthropic", help="AI provider: anthropic or openai"),
    context: str | None = typer.Option(None, help="Additional context for estimation"),
) -> None:
    """Get AI probability estimate for a market."""
    from kalshi_intel.analysis.probability import ProbabilityEstimator
    from kalshi_intel.config import get_settings

    settings = get_settings()
    client = _get_client()

    with console.status(f"Fetching market {ticker}..."):
        market = client.get_market(ticker)

    api_key = None
    if provider == "anthropic" and settings.anthropic_api_key:
        api_key = settings.anthropic_api_key.get_secret_value()
    elif provider == "openai" and settings.openai_api_key:
        api_key = settings.openai_api_key.get_secret_value()

    if not api_key:
        console.print(
            f"[red]No API key set for {provider}. "
            "Set KALSHI_ANTHROPIC_API_KEY or KALSHI_OPENAI_API_KEY.[/red]"
        )
        raise typer.Exit(1)

    estimator = ProbabilityEstimator(provider=provider, api_key=api_key)

    with console.status("Generating probability estimate..."):
        est = estimator.estimate(market, context=context)

    console.print(f"\n[bold]Market:[/bold] {est.market_ticker}")
    console.print(f"[bold]Estimated Probability:[/bold] {est.estimated_probability:.1%}")
    console.print(f"[bold]Confidence:[/bold] {est.confidence:.0%}")
    console.print(f"[bold]Edge vs Market:[/bold] {est.edge_vs_market:+.1%}")
    console.print(f"[bold]Model:[/bold] {est.model_used}")
    console.print(f"\n[bold]Reasoning:[/bold]\n{est.reasoning}")

    if est.key_factors:
        console.print("\n[bold]Key Factors:[/bold]")
        for f in est.key_factors:
            console.print(f"  - {f}")

    if est.data_gaps:
        console.print("\n[bold]Data Gaps:[/bold]")
        for g in est.data_gaps:
            console.print(f"  - {g}")

    _print_disclaimer()


# --- Market data commands ---


@app.command()
def market(
    ticker: str = typer.Argument(..., help="Market ticker"),
) -> None:
    """Display detailed market information."""
    from kalshi_intel.utils.money import format_cents

    client = _get_client()

    with console.status(f"Fetching market {ticker}..."):
        m = client.get_market(ticker)

    console.print(f"\n[bold cyan]{m.ticker}[/bold cyan]")
    console.print(f"[bold]Title:[/bold] {m.title or m.rules_primary}")
    console.print(f"[bold]Status:[/bold] {m.status.value}")
    console.print(
        f"[bold]YES Bid/Ask:[/bold] {format_cents(m.yes_bid)} / {format_cents(m.yes_ask)}"
    )
    console.print(f"[bold]NO Bid/Ask:[/bold] {format_cents(m.no_bid)} / {format_cents(m.no_ask)}")
    console.print(f"[bold]Last Price:[/bold] {format_cents(m.last_price)}")
    console.print(f"[bold]Spread:[/bold] {format_cents(m.spread_cents)}")
    console.print(f"[bold]Implied Prob:[/bold] {m.implied_probability:.1%}")
    console.print(f"[bold]Volume 24h:[/bold] {m.volume_24h}")
    console.print(f"[bold]Open Interest:[/bold] {m.open_interest}")
    console.print(f"[bold]Close Time:[/bold] {m.close_time}")

    if m.rules_primary:
        console.print(f"\n[bold]Rules:[/bold]\n{m.rules_primary}")


@app.command()
def orderbook(
    ticker: str = typer.Argument(..., help="Market ticker"),
    depth: int = typer.Option(10, help="Number of levels to show"),
) -> None:
    """Display current orderbook for a market."""
    from rich.table import Table

    client = _get_client()

    with console.status(f"Fetching orderbook for {ticker}..."):
        ob = client.get_orderbook(ticker, depth=depth)

    table = Table(title=f"Orderbook: {ticker}")
    table.add_column("YES Bids", style="green")
    table.add_column("Qty", style="green")
    table.add_column("NO Bids", style="red")
    table.add_column("Qty", style="red")

    max_rows = max(len(ob.yes), len(ob.no))
    for i in range(min(max_rows, depth)):
        yes_price = f"{ob.yes[i][0]}c" if i < len(ob.yes) else ""
        yes_qty = str(ob.yes[i][1]) if i < len(ob.yes) and len(ob.yes[i]) > 1 else ""
        no_price = f"{ob.no[i][0]}c" if i < len(ob.no) else ""
        no_qty = str(ob.no[i][1]) if i < len(ob.no) and len(ob.no[i]) > 1 else ""
        table.add_row(yes_price, yes_qty, no_price, no_qty)

    console.print(table)


# --- Portfolio commands ---


@app.command()
def balance() -> None:
    """Show current account balance."""
    from kalshi_intel.utils.money import format_dollars

    client = _get_client()
    bal = client.get_balance()
    console.print(f"\n[bold]Available Balance:[/bold] {format_dollars(bal.balance)}")
    console.print(f"[bold]Portfolio Value:[/bold] {format_dollars(bal.portfolio_value)}")


@app.command()
def positions() -> None:
    """Show current open positions."""
    from rich.table import Table

    client = _get_client()
    pos = client.get_positions()

    if not pos:
        console.print("[yellow]No open positions.[/yellow]")
        return

    table = Table(title="Open Positions")
    table.add_column("Ticker", style="cyan")
    table.add_column("Exposure")
    table.add_column("Realized P&L")

    for p in pos:
        table.add_row(
            p.ticker,
            str(p.market_exposure),
            str(p.realized_pnl),
        )
    console.print(table)


@app.command()
def pnl() -> None:
    """Show trade log P&L summary."""
    from kalshi_intel.reports.trade_log import TradeLog
    from kalshi_intel.utils.money import format_dollars

    log = TradeLog()
    summary = log.calculate_pnl()

    console.print("\n[bold]Trade Log P&L Summary[/bold]")
    console.print(f"  Total trades: {summary['total_trades']}")
    console.print(f"  Total cost: {format_dollars(summary['total_cost_cents'])}")
    console.print(f"  Total fees: {format_dollars(summary['total_fees_cents'])}")
    console.print(f"  Realized P&L: {format_dollars(summary['realized_pnl_cents'])}")
    console.print(
        f"  Win rate: {summary['win_rate']:.1%} ({summary['wins']}W / {summary['losses']}L)"
    )


# --- Report command ---


@app.command()
def report(
    with_ai: bool = typer.Option(False, help="Include AI probability estimates"),
    top_n: int = typer.Option(10, help="Number of top opportunities"),
    provider: str = typer.Option("anthropic", help="AI provider for estimates"),
) -> None:
    """Generate and save daily report."""
    from kalshi_intel.reports.daily_report import DailyReportGenerator
    from kalshi_intel.scanner.scanner import DailyScanner

    client = _get_client()
    scanner = DailyScanner(client=client, top_n=top_n)

    with console.status("Running scan..."):
        results = scanner.run()

    ai_estimates = None
    if with_ai and results:
        from kalshi_intel.analysis.probability import ProbabilityEstimator
        from kalshi_intel.config import get_settings

        settings = get_settings()
        api_key = None
        if provider == "anthropic" and settings.anthropic_api_key:
            api_key = settings.anthropic_api_key.get_secret_value()

        if api_key:
            estimator = ProbabilityEstimator(provider=provider, api_key=api_key)
            with console.status("Generating AI estimates..."):
                markets = [r.market for r in results[:5]]  # Top 5 only
                ai_estimates = estimator.batch_estimate(markets)

    gen = DailyReportGenerator()
    rpt = gen.generate(results, ai_estimates=ai_estimates)
    path = gen.save(rpt)

    console.print(f"[green]Report saved to {path}[/green]")
    _print_disclaimer()


# --- Watch command (WebSocket) ---


@app.command()
def watch(
    tickers: list[str] = typer.Argument(..., help="Market tickers to watch"),
) -> None:
    """Watch real-time price updates via WebSocket."""
    from kalshi_intel.client.websocket import KalshiWebSocketClient
    from kalshi_intel.config import get_settings
    from kalshi_intel.utils.money import format_cents

    settings = get_settings()

    auth = None
    if settings.api_key_id:
        from kalshi_intel.client.auth import KalshiAuthenticator

        auth = KalshiAuthenticator(settings.api_key_id, settings.private_key_path)

    async def _watch():
        ws = KalshiWebSocketClient(settings.ws_url, authenticator=auth)
        await ws.connect()

        def on_tick(ticker: str, yes_bid: int, yes_ask: int, volume: int):
            console.print(
                f"[cyan]{ticker}[/cyan] "
                f"YES: {format_cents(yes_bid)}/{format_cents(yes_ask)} "
                f"Vol: {volume}"
            )

        console.print(f"Watching {len(tickers)} market(s). Press Ctrl+C to stop.\n")
        try:
            await ws.listen_tickers(tickers, on_tick)
        except KeyboardInterrupt:
            await ws.close()

    asyncio.run(_watch())


# --- Hedge calculator ---


@app.command()
def hedge(
    entry_side: str = typer.Argument(..., help="Original side: yes or no"),
    entry_price: int = typer.Argument(..., help="Entry price in cents"),
    current_price: int = typer.Argument(..., help="Current YES price in cents"),
    contracts: int = typer.Option(1, help="Number of contracts"),
) -> None:
    """Calculate hedge to lock in profit."""
    from kalshi_intel.analysis.hedging import lock_in_profit
    from kalshi_intel.utils.money import format_dollars

    result = lock_in_profit(entry_side, entry_price, current_price, contracts)

    console.print("\n[bold]Hedge Analysis[/bold]")
    console.print(f"  Entry: {entry_side.upper()} @ {entry_price}c x {contracts}")
    console.print(f"  Current YES price: {current_price}c")
    console.print(f"  Net cost: {format_dollars(result.net_cost_cents)}")
    console.print(f"  Guaranteed payout: {format_dollars(result.guaranteed_payout_cents)}")
    console.print(f"  Max gain: {format_dollars(result.max_gain_cents)}")
    console.print(f"  Max loss: {format_dollars(result.max_loss_cents)}")
    console.print("\n[bold]Scenarios:[/bold]")
    for s in result.scenarios:
        console.print(f"  {s['outcome']}: {format_dollars(s['pnl_cents'])}")

    _print_disclaimer()


if __name__ == "__main__":
    app()
