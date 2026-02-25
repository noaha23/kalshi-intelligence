"""Position sizing using Kelly criterion for binary prediction markets.

Kelly criterion for binary contracts:
  f* = (b*p - q) / b
where:
  p = true probability of YES
  q = 1 - p
  b = net odds ratio = (100 - price) / price

Fractional Kelly (default 0.25x) reduces volatility at the cost of suboptimal growth.
"""

from dataclasses import dataclass

from kalshi_intel.analysis.fees import fee_per_contract_cents


@dataclass
class PositionSizeResult:
    """Result of a position sizing calculation."""

    side: str  # "yes" or "no"
    kelly_fraction: float  # raw Kelly fraction of bankroll
    adjusted_fraction: float  # after fractional Kelly multiplier
    recommended_contracts: int  # integer contract count
    max_cost_cents: int  # total cost at given price
    expected_value_cents: float  # EV per contract * count
    edge_pct: float  # true_prob - implied_prob
    price_cents: int  # entry price
    true_probability: float


def kelly_fraction_binary(true_probability: float, market_price_cents: int) -> float:
    """Kelly criterion for binary prediction market contracts.

    f* = (b*p - q) / b
    where b = (100 - price) / price, p = true_prob, q = 1-p

    Positive = bet YES at this price.
    Negative = bet NO (i.e., the NO side has edge).
    Zero = no edge, don't bet.
    """
    if market_price_cents <= 0 or market_price_cents >= 100:
        return 0.0
    if true_probability <= 0.0 or true_probability >= 1.0:
        return 0.0

    p = true_probability
    q = 1.0 - p
    price = market_price_cents / 100.0
    b = (1.0 - price) / price  # net odds

    if b <= 0:
        return 0.0

    return (b * p - q) / b


def fractional_kelly(
    true_probability: float,
    market_price_cents: int,
    fraction: float = 0.25,
) -> float:
    """Fractional Kelly: raw Kelly * fraction.

    Quarter-Kelly (0.25) is a common conservative default that captures
    ~75% of the growth rate with much lower variance.
    """
    return kelly_fraction_binary(true_probability, market_price_cents) * fraction


def calculate_position_size(
    true_probability: float,
    market_price_cents: int,
    bankroll_cents: int,
    kelly_multiplier: float = 0.25,
    max_position_pct: float = 0.05,
    is_maker: bool = True,
) -> PositionSizeResult:
    """Full position sizing calculation.

    1. Compute raw Kelly fraction
    2. Apply fractional Kelly multiplier
    3. Cap at max_position_pct of bankroll
    4. Deduct estimated fees from EV
    5. Convert to integer contract count

    Args:
        true_probability: Your estimated true probability (0-1)
        market_price_cents: Current market price in cents (1-99)
        bankroll_cents: Total bankroll in cents
        kelly_multiplier: Fractional Kelly multiplier (default 0.25)
        max_position_pct: Max fraction of bankroll per position
        is_maker: Whether you'll place maker orders (lower fees)

    Returns:
        PositionSizeResult with all details.
    """
    raw_kelly = kelly_fraction_binary(true_probability, market_price_cents)

    # Determine side
    if raw_kelly >= 0:
        side = "yes"
        price = market_price_cents
        implied = market_price_cents / 100.0
        edge = true_probability - implied
    else:
        side = "no"
        price = 100 - market_price_cents
        implied = 1.0 - (market_price_cents / 100.0)
        edge = (1.0 - true_probability) - implied
        raw_kelly = abs(raw_kelly)

    # Apply fractional Kelly
    adjusted = raw_kelly * kelly_multiplier

    # Cap at max position size
    adjusted = min(adjusted, max_position_pct)

    # Calculate contract count
    allocation_cents = int(bankroll_cents * adjusted)
    contracts = allocation_cents // price if price > 0 else 0

    # Calculate cost and EV
    cost = contracts * price
    fee = fee_per_contract_cents(price, is_maker)
    ev_per_contract = (edge * 100) - fee  # edge * payout - fee
    total_ev = ev_per_contract * contracts

    return PositionSizeResult(
        side=side,
        kelly_fraction=raw_kelly,
        adjusted_fraction=adjusted,
        recommended_contracts=contracts,
        max_cost_cents=cost,
        expected_value_cents=total_ev,
        edge_pct=edge,
        price_cents=price,
        true_probability=true_probability,
    )


def multi_position_kelly(
    positions: list[tuple[float, int]],
    bankroll_cents: int,
    kelly_multiplier: float = 0.25,
    max_total_exposure_pct: float = 0.20,
) -> list[PositionSizeResult]:
    """Kelly sizing for multiple simultaneous positions.

    Scales down all positions proportionally if total exposure exceeds limit.

    Args:
        positions: List of (true_probability, market_price_cents) tuples
        bankroll_cents: Total bankroll in cents
        kelly_multiplier: Fractional Kelly multiplier
        max_total_exposure_pct: Max total bankroll fraction across all positions
    """
    results = [
        calculate_position_size(prob, price, bankroll_cents, kelly_multiplier, max_position_pct=1.0)
        for prob, price in positions
    ]

    # Calculate total exposure
    total_fraction = sum(r.adjusted_fraction for r in results)

    if total_fraction > max_total_exposure_pct and total_fraction > 0:
        scale = max_total_exposure_pct / total_fraction
        results = [
            calculate_position_size(
                prob,
                price,
                bankroll_cents,
                kelly_multiplier * scale,
                max_position_pct=1.0,
            )
            for prob, price in positions
        ]

    return results
