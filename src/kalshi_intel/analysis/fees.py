"""Kalshi taker/maker fee calculator for binary contracts.

Fee formula:
  Taker: ceil(0.07 * C * P * (1 - P))
  Maker: ceil(0.0175 * C * P * (1 - P))

where C = contract count, P = price in dollars (price_cents / 100).

Fees are highest at P=0.50 (max uncertainty) and approach zero near 0.01 or 0.99.
S&P 500 / Nasdaq-100 markets use halved multipliers (0.035 / 0.00875).
"""

import math

TAKER_RATE = 0.07
MAKER_RATE = 0.0175
SP500_TAKER_RATE = 0.035
SP500_MAKER_RATE = 0.00875


def taker_fee_cents(count: int, price_cents: int, sp500: bool = False) -> int:
    """Calculate taker fee in cents.

    Args:
        count: Number of contracts.
        price_cents: Price per contract in cents (1-99).
        sp500: True for S&P 500 / Nasdaq-100 markets (halved fees).

    Returns:
        Total fee in cents (rounded up).
    """
    if price_cents <= 0 or price_cents >= 100 or count <= 0:
        return 0
    rate = SP500_TAKER_RATE if sp500 else TAKER_RATE
    p = price_cents / 100.0
    return math.ceil(rate * count * p * (1.0 - p))


def maker_fee_cents(count: int, price_cents: int, sp500: bool = False) -> int:
    """Calculate maker fee in cents.

    Args:
        count: Number of contracts.
        price_cents: Price per contract in cents (1-99).
        sp500: True for S&P 500 / Nasdaq-100 markets (halved fees).

    Returns:
        Total fee in cents (rounded up).
    """
    if price_cents <= 0 or price_cents >= 100 or count <= 0:
        return 0
    rate = SP500_MAKER_RATE if sp500 else MAKER_RATE
    p = price_cents / 100.0
    return math.ceil(rate * count * p * (1.0 - p))


def fee_per_contract_cents(price_cents: int, is_maker: bool = False) -> float:
    """Fee for a single contract (not rounded, for analysis)."""
    if price_cents <= 0 or price_cents >= 100:
        return 0.0
    rate = MAKER_RATE if is_maker else TAKER_RATE
    p = price_cents / 100.0
    return rate * p * (1.0 - p)


def max_fee_per_contract_cents(is_maker: bool = False) -> float:
    """Maximum fee occurs at P=0.50. Returns ~1.75c taker, ~0.44c maker."""
    rate = MAKER_RATE if is_maker else TAKER_RATE
    return rate * 0.25  # P*(1-P) maxes at 0.25 when P=0.5


def breakeven_edge(price_cents: int, is_maker: bool = False) -> float:
    """Minimum probability edge needed to break even after fees.

    Returns edge as a decimal (e.g., 0.02 = 2% edge needed).
    """
    if price_cents <= 0 or price_cents >= 100:
        return 0.0
    fee = fee_per_contract_cents(price_cents, is_maker)
    # Edge needed = fee / expected_payout
    # For buying YES at price P: payout if correct = (100-P) cents
    payout = 100 - price_cents
    return fee / payout if payout > 0 else float("inf")


def net_payout_cents(
    side: str,
    price_cents: int,
    count: int,
    result: str | None = None,
    is_maker: bool = False,
    sp500: bool = False,
) -> int:
    """Calculate net P&L in cents including fees.

    Args:
        side: "yes" or "no"
        price_cents: Entry price in cents
        count: Number of contracts
        result: "yes" or "no" for settled, None for cost basis only
        is_maker: Whether this was a maker order
        sp500: S&P 500 / Nasdaq market

    Returns:
        Net P&L in cents (negative = loss).
    """
    fee_fn = maker_fee_cents if is_maker else taker_fee_cents
    fee = fee_fn(count, price_cents, sp500)
    cost = price_cents * count

    if result is None:
        # Return negative cost basis (money spent)
        return -(cost + fee)

    if side == "yes":
        payout = 100 * count if result == "yes" else 0
    else:
        payout = 100 * count if result == "no" else 0

    return payout - cost - fee
