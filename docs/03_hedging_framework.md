# Hedging and Position Sizing Framework

## Overview

This document covers the mechanics of binary prediction market contracts on Kalshi and how to use hedging and position sizing to manage risk. Binary contracts settle at either $1.00 (YES) or $0.00 (NO), creating a fixed-payout structure that enables specific hedging strategies. The Kelly criterion -- adapted for binary markets -- provides a mathematically optimal position sizing framework, though fractional Kelly (0.25x) is recommended for practical use. The codebase implements these formulas in `src/kalshi_intel/analysis/hedging.py` and `src/kalshi_intel/analysis/position_sizing.py`.

---

## Fee Calculations

Kalshi fees follow a parabolic curve -- highest at 50c (maximum uncertainty), tapering to near zero at extreme prices.

### Standard Fee Formulas

**Taker fee (market orders):**

```
taker_fee = ceil(0.07 * C * P * (1 - P))
```

**Maker fee (limit orders resting on the book):**

```
maker_fee = ceil(0.0175 * C * P * (1 - P))
```

Where:
- `C` = contract count
- `P` = price as a decimal (price_cents / 100)
- `ceil()` = ceiling function (round up to nearest cent)

### S&P 500 / Nasdaq-100 Halved Rates

S&P 500 and Nasdaq-100 index markets use halved fee rates:

- **Taker:** `0.035` (instead of `0.07`)
- **Maker:** `0.00875` (instead of `0.0175`)

### Fee Behavior

The parabolic `P * (1 - P)` term means fees peak at P = 0.50 and approach zero at extreme prices:

| Price | P * (1-P) | Taker Fee (1 contract) | Maker Fee (1 contract) |
|-------|-----------|------------------------|------------------------|
| 5c | 0.0475 | 1c | 1c |
| 10c | 0.0900 | 1c | 1c |
| 25c | 0.1875 | 2c | 1c |
| 50c | 0.2500 | 2c (~1.75c raw) | 1c (~0.44c raw) |
| 75c | 0.1875 | 2c | 1c |
| 90c | 0.0900 | 1c | 1c |
| 95c | 0.0475 | 1c | 1c |

At P = 0.50, the maximum per-contract taker fee is approximately 1.75c (rounds up to 2c), and the maximum maker fee is approximately 0.44c (rounds up to 1c).

### Implementation

From `src/kalshi_intel/analysis/fees.py`:

```python
def taker_fee_cents(count: int, price_cents: int, sp500: bool = False) -> int:
    rate = SP500_TAKER_RATE if sp500 else TAKER_RATE  # 0.035 or 0.07
    p = price_cents / 100.0
    return math.ceil(rate * count * p * (1.0 - p))
```

### Breakeven Edge

The minimum edge needed to overcome fees at a given price:

```python
def breakeven_edge(price_cents: int, is_maker: bool = False) -> float:
    fee = fee_per_contract_cents(price_cents, is_maker)
    payout = 100 - price_cents
    return fee / payout if payout > 0 else float("inf")
```

Maker orders are strongly preferred for marginal-edge positions. At 50c with a 2% edge, the taker fee nearly eliminates the EV while the maker fee preserves most of it.

---

## Kelly Criterion for Binary Markets

The Kelly criterion maximizes the expected logarithmic growth rate of your bankroll over repeated bets.

### Formula

```
f* = (b * p - q) / b
```

Where:
- `f*` = optimal fraction of bankroll to bet
- `p` = your estimated true probability of YES
- `q` = 1 - p = true probability of NO
- `b` = net odds = (100 - price) / price

### Worked Example

```
Market YES price: 40c
Your estimated true probability: 55% (0.55)
b = (100 - 40) / 40 = 1.5
q = 1 - 0.55 = 0.45
f* = (1.5 * 0.55 - 0.45) / 1.5 = (0.825 - 0.45) / 1.5 = 0.25

Kelly says: bet 25% of your bankroll
```

### Negative Kelly

When the Kelly fraction is negative, it indicates the opposite side has edge. The `calculate_position_size()` function detects this and automatically flips to the NO side:

```python
raw_kelly = kelly_fraction_binary(true_probability=0.35, market_price_cents=40)
# raw_kelly is negative -> betting NO is the correct side
# calculate_position_size() handles this automatically
```

---

## Fractional Kelly

Full Kelly is theoretically optimal but practically dangerous. A slight miscalibration of your probability estimate leads to massive overbetting.

**Fractional Kelly applies a multiplier to the raw Kelly fraction:**

```
adjusted_fraction = raw_kelly * multiplier
```

| Multiplier | Growth Rate Captured | Variance Relative to Full Kelly | Recommendation |
|------------|---------------------|--------------------------------|----------------|
| 1.00x | 100% | Very high | Theoretical only |
| 0.50x | 75% | 50% | Aggressive |
| 0.25x | ~56% | 25% | **Recommended default** |
| 0.10x | ~19% | 10% | Very conservative |

### Why 0.25x Is Recommended

1. Captures a meaningful portion (~56%) of the theoretical growth rate
2. Survives probability estimation errors of +/- 10% without ruin
3. Keeps individual positions small enough that a total loss is survivable
4. Empirically, most practitioners cannot estimate probabilities better than +/- 5-10%

---

## Position Sizing Caps

On top of Kelly, hard caps prevent catastrophic losses:

| Rule | Default | Rationale |
|------|---------|-----------|
| Max single position | 5% of bankroll | No single bet can ruin you |
| Max total exposure | 20% of bankroll | Limits correlated risk across all positions |

These are enforced in `calculate_position_size()` and `multi_position_kelly()`:

```python
# Single position
result = calculate_position_size(
    true_probability=0.65,
    market_price_cents=50,
    bankroll_cents=100_000,
    kelly_multiplier=0.25,
    max_position_pct=0.05,  # hard cap at 5%
)

# Multiple simultaneous positions
results = multi_position_kelly(
    positions=[(0.65, 50), (0.70, 45), (0.55, 60)],
    bankroll_cents=100_000,
    kelly_multiplier=0.25,
    max_total_exposure_pct=0.20,  # scale down if total > 20%
)
```

When total exposure across all positions exceeds 20%, all positions are scaled down proportionally.

---

## PositionSizeResult Dataclass

The position sizing output:

```python
@dataclass
class PositionSizeResult:
    side: str                      # "yes" or "no"
    kelly_fraction: float          # raw Kelly fraction
    adjusted_fraction: float       # after multiplier and cap
    recommended_contracts: int     # number of contracts to buy
    max_cost_cents: int            # total cost in cents
    price_cents: int               # entry price per contract
    edge_pct: float                # estimated_prob - implied_prob
    expected_value_cents: float    # EV per contract after fees
```

---

## Binary Contract Hedging

### Lock-In-Profit Strategy

The most common hedging strategy locks in a guaranteed profit after a favorable price movement.

**Key identity:** `YES price + NO price = 100c` (always, by construction). Buying both YES at 60c and NO at 40c costs exactly 100c and guarantees a 100c payout -- zero profit, zero loss (before fees).

### How It Works

**Scenario:** You bought YES at 40c. The price has moved to 60c.

**Hedge:** Buy NO at the current NO price (100c - 60c = 40c), or equivalently, sell your YES at 60c.

**P&L calculation:**

```
Entry:    Bought YES at 40c (cost: 40c per contract)
Hedge:    Buy NO at 40c     (cost: 40c per contract)
Total cost: 80c per contract

If YES resolves: YES pays 100c, NO pays 0c. Net = 100c - 80c = +20c
If NO resolves:  YES pays 0c, NO pays 100c. Net = 100c - 80c = +20c

Guaranteed profit: 20c per contract (before fees)
```

### General Formula

```
Guaranteed profit = contracts * (current_price - entry_price)
```

For YES holders, the guaranteed profit equals the price movement. With fees:

```
profit_after_fees = guaranteed_profit - entry_fee - hedge_fee
```

### Implementation

From `src/kalshi_intel/analysis/hedging.py`:

```python
def lock_in_profit(
    entry_side: str,
    entry_price_cents: int,
    current_price_cents: int,
    contracts: int,
    is_maker: bool = False,
) -> HedgeResult:
```

**CLI usage:**

```bash
# Bought YES at 40c, price now 60c, 10 contracts
kalshi-intel hedge yes 40 60 --contracts 10
```

### HedgeResult Dataclass

```python
@dataclass
class HedgeResult:
    entry_side: str
    entry_price_cents: int
    current_price_cents: int
    contracts: int
    guaranteed_profit_cents: int   # before fees
    entry_fee_cents: int
    hedge_fee_cents: int
    net_profit_cents: int          # after both fees
    breakeven_price_cents: int     # minimum price for profitable hedge
```

---

## Breakeven Price for Hedging

The minimum price movement needed to hedge profitably after accounting for fees:

```python
from kalshi_intel.analysis.hedging import breakeven_price

# Bought YES at 40c -- what price must YES reach to hedge profitably?
bp = breakeven_price(entry_price_cents=40)
# Returns ~43 (need 3c movement to cover round-trip fees)
```

| Entry Price | Breakeven Hedge Price | Movement Needed |
|-------------|----------------------|-----------------|
| 10c | ~12c | 2c |
| 25c | ~28c | 3c |
| 50c | ~54c | 4c |
| 75c | ~78c | 3c |
| 90c | ~92c | 2c |

Fees are highest at 50c, so the breakeven movement is largest there.

---

## Arbitrage in Multivariate Events

In events with mutually exclusive outcomes (e.g., "Which month will unemployment peak?"), the sum of all YES prices should equal 100c. Deviations represent potential arbitrage.

### Detection

From `src/kalshi_intel/analysis/hedging.py`:

```python
from kalshi_intel.analysis.hedging import check_arbitrage

arb = check_arbitrage(markets)
# Returns:
# {
#     "sum_yes_cents": 97.5,
#     "mispricing_cents": 2.5,     # 100 - 97.5
#     "is_arbitrage": True,        # if mispricing > fees
#     "direction": "buy_all",      # buy all sides for guaranteed profit
#     "estimated_fee_cents": 1.8,  # total fees for buying all sides
#     "net_profit_cents": 0.7,     # guaranteed profit per set
#     "markets": [("TICKER-A", 30), ("TICKER-B", 25), ...]
# }
```

### Conditions

- `sum(YES prices) < 100`: Buy all YES contracts. Guaranteed one resolves YES, paying 100c. Cost = sum of prices. Profit = 100 - sum - fees.
- `sum(YES prices) > 100`: Sell all YES contracts (buy all NO). Guaranteed one resolves NO, paying 100c. Profit = sum - 100 - fees.
- The mispricing must exceed total fees for all legs to be a true arbitrage.

**Practical note:** True arbitrage on Kalshi is rare and short-lived. When it appears, it is usually in the 1-3c range and quickly corrected. Fees and execution risk often eliminate the profit. Manual execution is usually too slow.

---

## Worked Example: Full Lifecycle

**Setup:**
- Market: "Will CPI exceed 3.5% in March?"
- Bankroll: $1,000 (100,000 cents)
- Your estimate: 65% probability
- Current YES price: 50c

**Step 1: Position sizing (0.25x Kelly)**

```python
result = calculate_position_size(
    true_probability=0.65,
    market_price_cents=50,
    bankroll_cents=100_000,
    kelly_multiplier=0.25,
    max_position_pct=0.05,
)
# result.side = "yes"
# result.kelly_fraction = 0.30 (raw Kelly)
# result.adjusted_fraction = 0.05 (0.25 * 0.30 = 0.075, capped at 0.05)
# result.recommended_contracts = 100 (5000c / 50c per contract)
# result.max_cost_cents = 5000
```

**Step 2: Entry**

Buy 100 YES contracts at 50c. Cost = $50.00.
Taker fee = ceil(0.07 * 100 * 0.5 * 0.5) = ceil(1.75) = 2c total.

**Step 3: Price moves to 65c**

Check hedge profitability:

```
Guaranteed profit (before fees): 100 * (65 - 50) = 1500c ($15.00)
Entry fee: 2c
Hedge fee: ceil(0.07 * 100 * 0.35 * 0.65) = ceil(1.59) = 2c
Net profit after fees: 1500 - 2 - 2 = 1496c ($14.96)
```

**Step 4: Decision**

Three options:
1. **Hedge now:** Lock in $14.96 guaranteed profit regardless of outcome.
2. **Hold:** If YES resolves, profit = 100 * (100-50) - fees = $49.98. If NO, loss = $50.02.
3. **Partial hedge:** Hedge 50 contracts (lock in ~$7.48), hold 50 (still exposed to upside/downside).

---

## Multi-Position Kelly Example

**Setup:** $1,000 bankroll, three simultaneous opportunities:

| Market | Your Prob | Market Price | Edge |
|--------|-----------|-------------|------|
| CPI > 3.5% | 0.65 | 50c | +15% |
| Unemployment < 4% | 0.70 | 60c | +10% |
| Fed holds rate | 0.55 | 45c | +10% |

```python
results = multi_position_kelly(
    positions=[(0.65, 50), (0.70, 60), (0.55, 45)],
    bankroll_cents=100_000,
    kelly_multiplier=0.25,
    max_total_exposure_pct=0.20,
)
# Total Kelly fractions before cap: ~0.075 + 0.05 + 0.06 = 0.185
# Under 20% cap, so no scaling needed
# Position 1: 15 contracts @ 50c ($7.50)
# Position 2: 8 contracts @ 60c ($4.80)
# Position 3: 13 contracts @ 45c ($5.85)
# Total exposure: $18.15 (18.15% of bankroll)
```

---

## Position Sizing Decision Table

| Edge | Kelly (0.25x) | Effective Cap | Guidance | Confidence Required |
|------|---------------|---------------|----------|---------------------|
| < 2% | < 0.5% | 0.5% | Skip or tiny size | Very high |
| 2-5% | 0.5-2% | 2% | Small research position | High |
| 5-10% | 2-5% | 5% | Standard position | Moderate |
| 10-20% | 5%+ | 5% (capped) | Full position | Any |
| > 20% | 5% (capped) | 5% (capped) | Suspect your estimate | Review data |

**Edges above 20% should trigger skepticism.** Kalshi markets are reasonably efficient. If you think you have a 20%+ edge, either:
1. You have genuinely superior information (rare)
2. Your probability estimate is miscalibrated (common)
3. The market is illiquid and the price is stale (check volume)

---

## Fee Impact on Position Sizing

Fees reduce the effective edge, which reduces the Kelly fraction:

| Scenario | Taker EV/contract | Maker EV/contract | Difference |
|----------|-------------------|-------------------|------------|
| 50c, 5% edge | 5.00 - 1.75 = 3.25c | 5.00 - 0.44 = 4.56c | 1.31c |
| 50c, 2% edge | 2.00 - 1.75 = 0.25c | 2.00 - 0.44 = 1.56c | 1.31c |

At small edges (2%), the taker fee nearly eliminates the EV. Maker orders are strongly preferred.

---

## Risks and Considerations

- **Probability estimation error is the primary risk.** Kelly sizing assumes your probability estimate is correct. Overconfidence leads to oversizing and potential ruin.
- **Correlated positions.** The `multi_position_kelly()` function treats positions as independent. If your positions are all correlated (e.g., all "economy does well" bets), true exposure is higher than calculated.
- **Hedge execution risk.** Locking in profit requires executing the hedge at the current price. In fast-moving markets, the price may slip between decision and execution.
- **Fee drag on hedging.** Round-trip fees (entry + hedge) range from 1c to 4c per contract. For small price movements, fees can eliminate all profit.
- **Arbitrage is fleeting.** Multivariate arbitrage opportunities are typically corrected within minutes.
- **Bankroll definition.** Only include capital you can afford to lose entirely. Do not include emergency funds, retirement accounts, or borrowed money.
- **Ruin probability.** Even with 0.25x Kelly and 5% caps, a 10-trade losing streak at 5% per trade reduces your bankroll by 40%. This is not a risk-free system.
