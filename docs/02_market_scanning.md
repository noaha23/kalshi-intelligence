# Market Opportunity Scanning System

## Overview

The market scanning system automates the process of identifying potentially mispriced prediction market contracts on Kalshi. It fetches all active markets, applies a configurable filter chain to eliminate illiquid or unsuitable contracts, scores the remaining markets across five weighted factors, and ranks them by composite score. The system is designed to run daily (or on-demand) and surfaces the top N opportunities for further manual analysis and AI-assisted probability estimation.

---

## Daily Scanning Workflow

The `DailyScanner` class (`src/kalshi_intel/scanner/scanner.py`) orchestrates the end-to-end workflow:

```
1. Fetch all active markets (auto-paginated)
2. Apply filter chain (status, volume, OI, time, spread, price range)
3. Group filtered markets by event_ticker for hedgeability scoring
4. For each filtered market:
   a. Fetch orderbook (rate-limited, skip on failure)
   b. Score across 5 factors
5. Sort by composite score descending
6. Return top N results
```

Kalshi lists 500-2000+ active markets at any time. Without filtering, the signal-to-noise ratio is very low. The filter chain typically reduces the candidate set by 70-85%, leaving 100-400 markets for scoring. The full scan including orderbook fetches takes 3-8 minutes depending on how many markets pass filters (one API call per orderbook).

**CLI usage:**

```bash
# Default scan: top 20 opportunities
kalshi-intel scan

# Custom parameters
kalshi-intel scan --top-n 50 --min-volume 500 --save

# Scan a specific event
kalshi-intel scan-event ECON-CPI
```

**Programmatic usage:**

```python
from kalshi_intel.scanner.scanner import DailyScanner
from kalshi_intel.scanner.filters import default_filters
from kalshi_intel.scanner.scoring import ScoringWeights

scanner = DailyScanner(
    client=client,
    filters=default_filters(),
    weights=ScoringWeights(),
    top_n=20,
)
results = scanner.run()  # returns list[MarketScore]
```

---

## Filter Chain

Filters are applied sequentially. A market must pass ALL filters to be scored. Each filter implements an abstract base class:

```python
class MarketFilter(ABC):
    @abstractmethod
    def passes(self, market: Market) -> bool: ...

    @abstractmethod
    def description(self) -> str: ...
```

### Default Filter Predicates

The default chain is defined in `src/kalshi_intel/scanner/filters.py`:

| Filter | Default Threshold | Rationale |
|--------|-------------------|-----------|
| `StatusFilter` | `["active"]` | Only tradable markets |
| `MinVolumeFilter` | 24h volume >= 50 | Ensure enough activity to enter/exit |
| `MinOpenInterestFilter` | OI >= 20 | Ensure existing market depth |
| `MinDaysToCloseFilter` | >= 1 day | Enough time to research and act |
| `MaxDaysToCloseFilter` | <= 90 days | Avoid excessive capital lockup |
| `SpreadFilter` | Spread <= 20c | Avoid illiquid markets with wide spreads |
| `PriceRangeFilter` | 5c-95c | Exclude extreme longshots and near-certainties |

### Customizing Filters

```python
from kalshi_intel.scanner.filters import (
    StatusFilter,
    MinVolumeFilter,
    MinOpenInterestFilter,
    MaxDaysToCloseFilter,
    SpreadFilter,
    PriceRangeFilter,
)

# Tighter filters for high-conviction scanning
tight_filters = [
    StatusFilter(allowed_statuses=["active"]),
    MinVolumeFilter(min_volume_24h=500),
    MinOpenInterestFilter(min_oi=200),
    MaxDaysToCloseFilter(max_days=30),
    SpreadFilter(max_spread_cents=5),
    PriceRangeFilter(min_price=20, max_price=80),
]
```

Adding custom filters is straightforward -- implement the `MarketFilter` abstract class with `passes()` and `description()` methods. For example, a category filter, keyword filter, or event-based filter.

---

## Multi-Factor Scoring Rubric

Each market is scored on a 0.0 to 1.0 scale across five factors. The composite score is the weighted sum of all factor scores.

### Default Weights

Defined in `src/kalshi_intel/scanner/scoring.py`:

| Factor | Weight | What It Measures |
|--------|--------|-----------------|
| Liquidity | 0.30 (30%) | Can you enter/exit at a fair price? |
| Mispricing Potential | 0.25 (25%) | Is the price in the uncertain zone where edge is most likely? |
| Data Availability | 0.20 (20%) | Are there public data sources to form an independent estimate? |
| Time to Resolution | 0.15 (15%) | Is the time horizon in the sweet spot? |
| Hedgeability | 0.10 (10%) | Are there related markets to spread risk? |

### Liquidity Score (30% weight)

Combines volume, open interest, spread, and orderbook depth using log scaling:

```
liquidity = (volume_score * 0.3) + (oi_score * 0.3) + (spread_score * 0.25) + (depth_score * 0.15)
```

| Sub-Factor | Scoring Thresholds |
|------------|-------------------|
| 24h Volume | 25=0.25, 100=0.5, 500=0.75, 1000+=1.0 (log-scaled) |
| Open Interest | 10=0.25, 50=0.5, 200=0.75, 500+=1.0 (log-scaled) |
| Spread | <=3c=1.0, <=5c=0.75, <=10c=0.5, <=15c=0.25 |
| Orderbook Depth | 50+=0.5, 200+=0.75, 500+=1.0 |

Log scaling ensures that the difference between 100 and 200 volume is weighted more heavily than the difference between 1000 and 1100, reflecting the diminishing marginal benefit of additional liquidity.

### Mispricing Potential Score (25% weight)

Markets near 50c (maximum uncertainty) have the highest potential for finding edge. The score peaks at 50c and falls off symmetrically using a power function:

```python
distance = abs(mid - 50) / 50.0
score = 1.0 - (distance ** 1.5)
```

This penalizes extreme prices (near 5c or 95c) where:
- Fees eat most of the potential profit
- The event is nearly certain/impossible
- The risk/reward ratio is unfavorable

A market at 50c scores 1.0; a market at 25c or 75c scores approximately 0.65; a market at 10c or 90c scores approximately 0.28.

### Data Availability Score (20% weight)

Checks the market's category and rule text against known public data sources. Categories with verifiable, quantitative data sources score highest:

```python
CATEGORY_DATA_SOURCES = {
    "economics": ["BLS (CPI, Jobs)", "FRED", "Atlanta Fed GDPNow", "CME FedWatch"],
    "weather": ["NOAA/NWS", "Weather Underground", "ECMWF", "GFS models"],
    "politics": ["FiveThirtyEight", "RealClearPolitics", "The Economist", "Polling aggregators"],
    "financials": ["Yahoo Finance", "Bloomberg", "CME Group", "CBOE VIX"],
    "crypto": ["CoinGecko", "Binance API", "Glassnode", "Funding rates"],
    "transportation": ["TSA checkpoint data (daily)", "DOT statistics"],
    "sports": ["ESPN", "The Odds API", "team stats databases"],
}
```

Economics and weather categories score highest because they rely on official government data releases and numerical weather models. Politics scores medium. Keywords in the rules text (e.g., "cpi", "temperature", "bitcoin") boost the score further.

### Time to Resolution Score (15% weight)

The sweet spot is 7-30 days -- enough time to research but not so long that capital is locked up inefficiently:

| Days to Close | Score | Rationale |
|---------------|-------|-----------|
| 0 | 0.0 | Expired |
| 1-2 | 0.3 | Too late to research |
| 3-7 | 0.7 | Viable but rushed |
| 8-14 | 1.0 | Optimal zone |
| 15-30 | 0.9 | Good with more uncertainty |
| 31-60 | 0.6 | Capital locked longer |
| 61-90 | 0.4 | High uncertainty, poor capital efficiency |
| 90+ | 0.2 | Too far out |

### Hedgeability Score (10% weight)

Based on the number of related markets in the same event:

| Related Markets | Score |
|-----------------|-------|
| 0 (standalone) | 0.3 |
| 1-2 | 0.6 |
| 3-4 | 0.8 |
| 5+ | 1.0 |

Markets within multivariate events (e.g., "Which month will CPI peak?") score highest because correlated contracts enable natural hedging and arbitrage detection.

---

## MarketScore Dataclass

The scoring output for each market is captured in a structured dataclass:

```python
@dataclass
class MarketScore:
    market: Market
    liquidity_score: float        # 0.0 to 1.0
    mispricing_score: float       # 0.0 to 1.0
    data_availability_score: float # 0.0 to 1.0
    time_score: float             # 0.0 to 1.0
    hedgeability_score: float     # 0.0 to 1.0
    composite_score: float        # weighted sum, 0.0 to 1.0
```

This allows downstream consumers (reporting, AI estimation, position sizing) to inspect individual subscores and understand why a market was ranked highly.

---

## Category Data Source Mappings

### Full Source Registry

| Category | Source | URL | Data Provided |
|----------|--------|-----|---------------|
| Economics | BLS CPI | bls.gov/cpi/ | CPI, inflation rates |
| Economics | BLS Employment | bls.gov/ces/ | Jobs, unemployment |
| Economics | BEA GDP | bea.gov | GDP growth |
| Economics | FRED | fred.stlouisfed.org | All economic indicators |
| Economics | CME FedWatch | cmegroup.com | Fed rate probabilities |
| Economics | Atlanta Fed GDPNow | atlantafed.org | Real-time GDP estimates |
| Weather | NOAA/NWS | weather.gov | Forecasts, temperatures |
| Weather | Weather Underground | wunderground.com | Detailed local forecasts |
| Weather | ECMWF | ecmwf.int | European weather models |
| Weather | GFS | ncep.noaa.gov | Global Forecast System models |
| Politics | FiveThirtyEight | fivethirtyeight.com | Polls, forecasting models |
| Politics | RealClearPolitics | realclearpolitics.com | Polling averages |
| Financials | Yahoo Finance | finance.yahoo.com | Stock prices, indices |
| Financials | CBOE | cboe.com | VIX, options data |
| Crypto | CoinGecko | coingecko.com | Crypto prices, market caps |
| Crypto | Binance API | api.binance.com | Real-time crypto trading data |
| Transportation | TSA | tsa.gov | Daily checkpoint throughput numbers |
| Sports | ESPN | espn.com | Scores, stats, schedules |
| Sports | The Odds API | the-odds-api.com | Aggregated betting odds |

### Category Edge Assessment

- **Economics**: Highest exploitable edge. Data is publicly available but requires quantitative analysis. Many Kalshi participants rely on intuition rather than models. Markets often lag FRED data by hours after releases.
- **Weather**: Strong edge potential. Weather models update every 6-12 hours. Kalshi prices often reflect yesterday's forecast.
- **Politics**: Moderate edge. Markets attract sophisticated participants and high volume. Edges are smaller and more contested.
- **Sports**: Lowest edge on Kalshi. Professional bettors and automated systems set prices quickly. Only recommended with a specialized model.

---

## Optimal Scan Times

| Time (ET) | Rationale |
|-----------|-----------|
| 6:00-7:00 AM | Pre-market: catch overnight mispricings before US traders wake up |
| 8:30-9:00 AM | After BLS/economic data releases (CPI, jobs usually at 8:30 AM) |
| 12:00-1:00 PM | Midday lull: prices may drift as attention wanes |
| 2:00-2:30 PM | After FOMC announcements (when scheduled) |
| 9:00-10:00 PM | After market close: catch late-day data releases |

Early morning scans (6-8 AM ET) and post-data-release scans catch the widest mispricings before the market adjusts.

---

## DailyScanner Orchestrator

The `DailyScanner` class ties together the filter chain, scoring rubric, and API client:

```python
class DailyScanner:
    def __init__(
        self,
        client: KalshiRestClient,
        filters: list[MarketFilter],
        weights: ScoringWeights,
        top_n: int = 20,
    ): ...

    def run(self) -> list[MarketScore]:
        """Execute the full scan pipeline."""
        ...
```

Key behaviors:
- Auto-paginates through all active markets
- Applies filters in sequence, short-circuiting on first failure
- Groups markets by `event_ticker` before scoring hedgeability
- Fetches orderbooks one at a time (rate-limited), skipping on failure
- Returns results sorted by composite score descending

---

## Automation with Cron

**Daily morning scan:**

```cron
# Run daily scan at 6:30 AM ET, save report
30 6 * * * cd /path/to/kalshi-intelligence && kalshi-intel scan --top-n 30 --save 2>&1 >> logs/scan.log
```

**Post-CPI release scan:**

```bash
# Run immediately after CPI release
kalshi-intel scan --top-n 10 --min-volume 50 --save
```

**Weekly full report with AI estimates:**

```cron
# Sunday evening: generate full report with AI estimates for the week ahead
0 20 * * 0 cd /path/to/kalshi-intelligence && kalshi-intel report --with-ai --top-n 15 2>&1 >> logs/report.log
```

---

## Customizing Weights

If you specialize in a particular category, adjust weights accordingly:

```python
# Economics specialist: increase data_availability weight
weights = ScoringWeights(
    liquidity=0.20,
    mispricing_potential=0.25,
    data_availability=0.30,
    time_to_resolution=0.15,
    hedgeability=0.10,
)
```

---

## Risks and Considerations

- **Stale data.** The scan fetches a snapshot in time. By the time you review results, prices may have moved. Always re-check before acting.
- **Orderbook fetch latency.** Fetching orderbooks for 200+ markets is rate-limited. Markets scanned last may have prices that shifted during the scan window.
- **False positives.** A high composite score does not mean there is actual mispricing. The scoring rubric identifies markets with good characteristics for analysis, not markets with confirmed edge.
- **Category bias.** The `data_availability` scorer is biased toward categories with entries in `CATEGORY_DATA_SOURCES`. Markets in unlisted categories receive a low base score even if data sources exist.
- **Volume manipulation.** In thin markets, a single large order can temporarily distort volume and price metrics. The `MinOpenInterestFilter` partially mitigates this.
- **Time zone sensitivity.** All time calculations use UTC. Cron jobs should be configured in the appropriate timezone for your data release schedule.
- **API cost.** Each full scan makes hundreds of API calls (markets list + one orderbook per filtered market). Monitor your rate limit tier and consider batching strategies.
