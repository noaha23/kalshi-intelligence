"""Hedge formulas for binary prediction market contracts.

Key insight: In a binary market, YES + NO always = $1.00.
If YES is priced at 60c and NO at 40c, buying both sides costs $1.00
and guarantees $1.00 payout -- no profit. Edge comes from:
1. Finding mispriced contracts where YES + NO < $1.00 (arbitrage)
2. Spreading across correlated contracts in the same event
3. Hedging with partial positions to lock in profit after price movement
"""

from dataclasses import dataclass, field

from kalshi_intel.analysis.fees import taker_fee_cents
from kalshi_intel.client.models import Market


@dataclass
class HedgePosition:
    """A single leg of a hedge."""

    market_ticker: str
    side: str  # "yes" or "no"
    contracts: int
    price_cents: int
    cost_cents: int


@dataclass
class HedgeResult:
    """Complete hedge analysis for a position."""

    primary: HedgePosition
    hedges: list[HedgePosition]
    net_cost_cents: int
    guaranteed_payout_cents: int
    max_loss_cents: int
    max_gain_cents: int
    scenarios: list[dict] = field(default_factory=list)


def lock_in_profit(
    entry_side: str,
    entry_price_cents: int,
    current_price_cents: int,
    contracts: int,
    is_maker: bool = False,
) -> HedgeResult:
    """Calculate hedge to lock in profit after price has moved favorably.

    Example: Bought YES at 40c, price moved to 60c.
    Sell YES at 60c (or equivalently, buy NO at 40c) to lock in the spread.

    Args:
        entry_side: Original position side ("yes" or "no")
        entry_price_cents: Original entry price
        current_price_cents: Current market price for YES
        contracts: Number of contracts in original position
        is_maker: Whether hedge order will be maker
    """
    if entry_side == "yes":
        # Bought YES at entry_price, now YES is at current_price
        # Hedge: sell YES at current_price (= buy NO at 100-current_price)
        hedge_side = "no"
        hedge_price = 100 - current_price_cents
        hedge_cost = hedge_price * contracts

        # Both scenarios pay 100*contracts, so net = contracts * (current - entry)
        guaranteed = contracts * (current_price_cents - entry_price_cents)
    else:
        # Bought NO at entry_price (= 100 - yes_price at time)
        # YES was at (100 - entry_price) when we entered
        # Now YES is at current_price, so NO is at (100 - current_price)
        hedge_side = "yes"
        hedge_price = current_price_cents
        hedge_cost = hedge_price * contracts

        # Guaranteed: contracts * ((100-current_price) from NO side was cheaper)
        # Entry NO price = entry_price_cents, current NO price = 100-current_price
        # If NO price went down (favorable for us as NO holder -- wait, no)
        # Actually for NO: we want the underlying to be NO, so if YES price drops,
        # our NO position gains value.
        # Hedge: buy YES at current_price
        # If YES resolves: YES pays 100*C, NO pays 0. Net = 100*C - entry_cost - hedge_cost
        # If NO resolves: NO pays 100*C, YES pays 0. Net = 100*C - entry_cost - hedge_cost
        # Both: 100*C - (entry_price + current_price)*C
        guaranteed = contracts * (100 - entry_price_cents - current_price_cents)

    # Account for fees
    entry_fee = taker_fee_cents(contracts, entry_price_cents)
    hedge_fee = taker_fee_cents(contracts, hedge_price if entry_side == "yes" else hedge_price)
    total_fees = entry_fee + hedge_fee
    guaranteed_after_fees = guaranteed - total_fees

    primary = HedgePosition(
        market_ticker="",
        side=entry_side,
        contracts=contracts,
        price_cents=entry_price_cents,
        cost_cents=entry_price_cents * contracts,
    )

    hedge = HedgePosition(
        market_ticker="",
        side=hedge_side,
        contracts=contracts,
        price_cents=hedge_price if entry_side == "yes" else current_price_cents,
        cost_cents=hedge_cost if entry_side == "yes" else current_price_cents * contracts,
    )

    return HedgeResult(
        primary=primary,
        hedges=[hedge],
        net_cost_cents=primary.cost_cents + hedge.cost_cents + total_fees,
        guaranteed_payout_cents=100 * contracts,
        max_loss_cents=max(0, -guaranteed_after_fees),
        max_gain_cents=max(0, guaranteed_after_fees),
        scenarios=[
            {"outcome": "YES resolves", "pnl_cents": guaranteed_after_fees},
            {"outcome": "NO resolves", "pnl_cents": guaranteed_after_fees},
        ],
    )


def check_arbitrage(markets: list[Market]) -> dict:
    """Check if YES prices across mutually exclusive markets in an event don't sum to 100.

    In a multivariate event with N mutually exclusive outcomes,
    the sum of all YES prices should equal ~100 cents.
    If sum < 100: buy all sides for guaranteed profit.
    If sum > 100: sell all sides for guaranteed profit.

    Returns:
        {
            "sum_yes_cents": total sum of YES mid prices,
            "mispricing_cents": deviation from 100,
            "is_arbitrage": True if |mispricing| > fee threshold,
            "direction": "buy_all" or "sell_all" or None,
            "markets": list of (ticker, price) tuples,
        }
    """
    if not markets:
        return {"sum_yes_cents": 0, "mispricing_cents": 0, "is_arbitrage": False}

    prices = [(m.ticker, m.mid_price_cents) for m in markets]
    total = sum(p for _, p in prices)
    mispricing = 100 - total

    # Estimate total fees for buying all sides
    total_fee = sum(taker_fee_cents(1, int(p)) for _, p in prices if 0 < p < 100)

    is_arb = abs(mispricing) > total_fee and abs(mispricing) > 2

    direction = None
    if is_arb:
        direction = "buy_all" if mispricing > 0 else "sell_all"

    return {
        "sum_yes_cents": total,
        "mispricing_cents": mispricing,
        "is_arbitrage": is_arb,
        "direction": direction,
        "estimated_fee_cents": total_fee,
        "net_profit_cents": abs(mispricing) - total_fee if is_arb else 0,
        "markets": prices,
    }


def breakeven_price(entry_price_cents: int, is_maker: bool = False) -> int:
    """Minimum price movement needed to break even after hedging with fees.

    If you bought YES at entry_price_cents, what price does YES need to
    reach before you can hedge and lock in profit after fees?
    """
    # You need: current_price - entry_price > 2 * fee_per_contract
    # Because you pay fees on both entry and hedge
    from kalshi_intel.analysis.fees import fee_per_contract_cents

    entry_fee = fee_per_contract_cents(entry_price_cents, is_maker)
    # Iterate to find breakeven (fee changes with price)
    for delta in range(1, 100):
        hedge_price = entry_price_cents + delta
        if hedge_price >= 100:
            return 99
        hedge_fee = fee_per_contract_cents(100 - hedge_price, is_maker)
        total_fee = entry_fee + hedge_fee
        if delta > total_fee:
            return hedge_price

    return 99
