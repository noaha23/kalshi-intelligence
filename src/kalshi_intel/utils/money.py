"""Cents/dollars conversion helpers."""


def cents_to_dollars(cents: int) -> float:
    """Convert cents to dollars."""
    return cents / 100.0


def dollars_to_cents(dollars: float) -> int:
    """Convert dollars to cents (rounded)."""
    return round(dollars * 100)


def format_dollars(cents: int) -> str:
    """Format cents as dollar string (e.g., 1234 -> '$12.34')."""
    return f"${cents / 100:.2f}"


def format_cents(cents: int) -> str:
    """Format cents with suffix (e.g., 50 -> '50c')."""
    return f"{cents}c"


def format_pnl(cents: int) -> str:
    """Format P&L with sign and color hint."""
    if cents >= 0:
        return f"+${cents / 100:.2f}"
    return f"-${abs(cents) / 100:.2f}"
