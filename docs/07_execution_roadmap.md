# 30-Day Execution Roadmap

> **Disclaimer:** This document is for educational and research purposes only. It does not constitute financial, investment, or trading advice. Trading event contracts involves risk of loss. Only trade with capital you can afford to lose. Past performance does not guarantee future results.

---

## Overview

This roadmap provides a structured 30-day plan to build a functioning Kalshi Market Intelligence System from the ground up. The four-week structure moves progressively from foundation (API client, models, CI) through analysis (Kelly criterion, scanning, hedging) to intelligence (AI estimation, external data, reports) and finally polish (calibration, logging, documentation, paper trading). The goal at Day 30 is a repeatable, data-driven process -- not profitability.

---

## Week 1: Foundation (Days 1-7)

**Goal:** Repository set up, CI passing, API client operational with authentication, fee calculator validated, basic data models in place.

### Day-by-Day Plan

| Day | Task | Output |
|---|---|---|
| 1 | Set up repository structure, `pyproject.toml`, dependencies (`httpx`, `pydantic`, `click`) | Clean project scaffold with `uv` package management |
| 2 | Configure CI pipeline: linting (`ruff`), type checking (`mypy`), test runner (`pytest`) | Passing CI on push/PR |
| 3 | Implement API client: authentication (API key + session management), base HTTP client | `KalshiClient` class with auth flow |
| 4 | Add REST endpoint methods: markets, events, orderbook, portfolio, orders | Full API coverage with typed responses |
| 5 | Implement pagination helpers and rate limiting (respect Kalshi's published limits) | Reliable bulk data retrieval |
| 6 | Build fee calculator: model Kalshi's fee schedule, compute round-trip costs per trade | `FeeCalculator` with tests validated against known fee examples |
| 7 | Define core data models (`Market`, `Position`, `Order`, `Portfolio`) with Pydantic | Type-safe data layer; demo API test suite passing |

### Week 1 Deliverables

- [ ] Repository with clean project structure and dependency management
- [ ] CI pipeline running on every push (lint, type check, test)
- [ ] `KalshiClient` with authentication, REST methods, pagination, rate limiting
- [ ] Fee calculator with unit tests matching Kalshi's published fee schedule
- [ ] Core Pydantic models for market data, positions, and orders
- [ ] Demo API connectivity test passing against Kalshi's demo environment

### Week 1 Success Criteria

| Metric | Target |
|---|---|
| CI status | All checks passing |
| API endpoints covered | Markets, events, orderbook, portfolio, orders |
| Fee calculator accuracy | Within $0.01 of actual Kalshi fees |
| Test coverage | Core client and fee calculator fully tested |
| Demo API | Authenticated and returning data |

---

## Week 2: Analysis Layer (Days 8-14)

**Goal:** Kelly criterion position sizing operational, market scanner with configurable filters and scoring, hedging framework for binary contracts, CLI commands for core functions.

### Day-by-Day Plan

| Day | Task | Output |
|---|---|---|
| 8 | Implement Kelly criterion position sizing: full Kelly, fractional Kelly (1/4, 1/2), edge/odds inputs | `PositionSizer` class with Kelly variants |
| 9 | Build bankroll management: max position size, max portfolio exposure, drawdown limits | Risk management layer integrated with position sizer |
| 10 | Implement market scanner: configurable filters (category, liquidity, spread, time-to-expiry) | `MarketScanner` class pulling live data and filtering |
| 11 | Add scoring system: rank opportunities by estimated edge, liquidity, fee-adjusted expected value | Scored and sorted market opportunities |
| 12 | Build hedging framework for binary contracts: correlated position identification, hedge ratio calculation | `HedgingEngine` with binary contract hedge strategies |
| 13 | Implement CLI commands: `fees` (calculate fees), `position-size` (Kelly sizing), `hedge` (suggest hedges) | Working CLI with `click` commands |
| 14 | Integration testing: end-to-end flow from scan to score to size | All Week 2 components tested together |

### Week 2 Deliverables

- [ ] Kelly criterion position sizer with fractional variants
- [ ] Market scanner with category, liquidity, spread, and expiry filters
- [ ] Scoring system ranking opportunities by fee-adjusted expected value
- [ ] Hedging framework identifying correlated positions and computing hedge ratios
- [ ] CLI commands: `fees`, `position-size`, `hedge`, `scan`
- [ ] Integration tests covering scan-to-size pipeline

### CLI Command Reference (Week 2)

```bash
# Calculate fees for a trade
kalshi-intel fees --price 0.65 --quantity 10 --side yes

# Compute position size using Kelly criterion
kalshi-intel position-size --edge 0.10 --probability 0.60 --bankroll 500 --kelly-fraction 0.25

# Suggest hedges for current portfolio
kalshi-intel hedge --portfolio-file portfolio.json

# Run market scan with filters
kalshi-intel scan --categories weather,economics --min-liquidity 100 --max-spread 0.10
```

### Week 2 Success Criteria

| Metric | Target |
|---|---|
| Position sizer | Produces correct Kelly fractions for test scenarios |
| Scanner | Returns filtered, scored markets from live API |
| Hedging | Identifies correlated positions and suggests hedge trades |
| CLI | All 4 commands functional with help text |
| Tests | Integration test passes end-to-end |

---

## Week 3: Intelligence (Days 15-21)

**Goal:** AI probability estimation with prompt engineering, external data source integration (FRED, BLS), daily report generation, WebSocket real-time price monitoring.

### Day-by-Day Plan

| Day | Task | Output |
|---|---|---|
| 15 | Implement AI probability estimation: prompt engineering for structured probability output | `ProbabilityEstimator` using LLM with calibrated prompts |
| 16 | Build prompt template library: category-specific prompts (economics, weather, finance, politics) | Prompt templates with structured output parsing |
| 17 | Integrate external data sources: FRED API (economic time series), BLS API (CPI, jobs data) | `DataSourceManager` pulling live economic data |
| 18 | Add additional data sources: NOAA weather API, TSA checkpoint data, Yahoo Finance | Multi-source data pipeline feeding into estimator |
| 19 | Build daily report generator: markdown + JSON output with top opportunities, portfolio status, market summary | `ReportGenerator` producing daily intelligence reports |
| 20 | Implement WebSocket real-time price monitoring: connect to Kalshi WebSocket, track price changes, alert on threshold moves | `PriceMonitor` with configurable alerts |
| 21 | Integration: wire data sources into AI estimator, feed estimates into scanner scoring, generate first full report | End-to-end intelligence pipeline producing daily report |

### Week 3 Deliverables

- [ ] AI probability estimator with category-specific prompt templates
- [ ] FRED API integration (800,000+ economic time series)
- [ ] BLS API integration (CPI, employment, PPI)
- [ ] NOAA weather data integration
- [ ] TSA checkpoint data pipeline
- [ ] Yahoo Finance integration for financial market data
- [ ] Daily report generator (markdown + JSON formats)
- [ ] WebSocket price monitor with configurable alerts
- [ ] CLI commands: `estimate`, `report`, `monitor`

### Prompt Engineering Approach

The AI probability estimator uses structured prompts that:

1. **Provide context:** Market description, contract terms, settlement criteria.
2. **Supply data:** Relevant external data (FRED series, BLS releases, NOAA forecasts).
3. **Request structured output:** Probability estimate (0-100%), confidence level, key factors, data sources consulted.
4. **Enforce calibration:** Include calibration instructions ("a 70% estimate should resolve YES approximately 70% of the time").
5. **Category-specific framing:** Economics prompts reference base rates and historical distributions; weather prompts reference ensemble model spreads; finance prompts reference options-implied probabilities.

### External Data Source Integration

| Source | API | Data Retrieved | Use Case |
|---|---|---|---|
| FRED | REST (free API key) | Economic time series (GDP, CPI, unemployment, rates) | Economics market estimation |
| BLS | REST (free) | Latest release data, revision history | CPI/jobs market estimation |
| NOAA | REST (free) | Forecasts, historical observations, ensemble data | Weather market estimation |
| TSA | Web scrape / structured data | Daily checkpoint throughput | Transportation market estimation |
| Yahoo Finance | REST / `yfinance` library | Stock prices, VIX, earnings data | Finance market estimation |

### Week 3 Success Criteria

| Metric | Target |
|---|---|
| AI estimates | Producing structured probability outputs for 5+ market categories |
| Data sources | At least 3 external sources returning live data |
| Daily report | Generating complete markdown + JSON report |
| WebSocket | Connected and receiving real-time price updates |
| Estimate quality | Within 15% of market price on average (initial calibration) |

---

## Week 4: Polish & Deploy (Days 22-30)

**Goal:** Historical calibration analysis, trade logging with P&L tracking, comprehensive documentation and test suite, paper trading validation against demo API.

### Day-by-Day Plan

| Day | Task | Output |
|---|---|---|
| 22 | Build historical calibration analysis: compare past estimates to outcomes, compute Brier scores | `CalibrationAnalyzer` with scoring and visualization |
| 23 | Implement calibration curve plotting and overconfidence detection | Calibration diagnostics identifying systematic biases |
| 24 | Build trade logging system: SQLite or JSON-based trade journal with full field coverage | `TradeLogger` capturing all required fields per trade |
| 25 | Add P&L tracking: per-trade, per-category, cumulative, with fee breakdowns | P&L dashboard data accessible via CLI |
| 26 | Write comprehensive documentation: README, API reference, configuration guide | Complete user-facing documentation |
| 27 | Expand test suite: unit tests for all modules, integration tests, edge case coverage | Test coverage > 80% on core modules |
| 28 | Paper trading validation: run full pipeline against Kalshi demo API for 3 consecutive days | Paper trades logged with real (demo) market data |
| 29 | Paper trading Day 2 + bug fixes and iteration based on paper trading observations | Refined pipeline based on live feedback |
| 30 | Paper trading Day 3 + 30-day retrospective: document what works, what does not, forward plan | Final paper trading results + retrospective document |

### Week 4 Deliverables

- [ ] Historical calibration analysis with Brier score computation
- [ ] Calibration curve plotting and overconfidence detection
- [ ] Trade logging system with complete field coverage
- [ ] P&L tracking: per-trade, per-category, cumulative
- [ ] Comprehensive documentation (README, API reference, config guide)
- [ ] Test suite with >80% coverage on core modules
- [ ] 3 days of paper trading against demo API with logged results
- [ ] 30-day retrospective document

### Paper Trading Validation Protocol

Paper trading uses the Kalshi demo API to simulate real trading conditions:

1. **Use real market data.** The demo API returns actual market prices and orderbooks.
2. **Apply real sizing.** Use Kelly criterion with a hypothetical $500 bankroll.
3. **Include fees.** Subtract estimated fees from every trade's P&L.
4. **Log everything.** Every scan result, estimate, sizing decision, and trade goes in the log.
5. **No hindsight adjustments.** Once a paper trade is logged, it is immutable.
6. **Compare to market.** Track whether your estimates were closer to outcomes than market prices.

### Week 4 Success Criteria

| Metric | Target |
|---|---|
| Calibration analysis | Completed with Brier score and calibration curve |
| Trade log | All paper trades captured with complete fields |
| P&L tracking | Accurate per-trade and cumulative figures |
| Test coverage | >80% on core modules |
| Documentation | README, API reference, and config guide complete |
| Paper trades | 3 days of logged paper trading results |

---

## Success Metrics (Day 30)

These are the measurable criteria for evaluating whether the 30-day build was successful. Success is defined by process quality, not profitability.

| Metric | Target | How to Measure |
|---|---|---|
| Daily scan operational | Running daily and producing ranked results | Scanner returns filtered, scored markets each day |
| Category coverage | 5+ categories with at least one data source each | Economics, weather, finance, politics, transportation all have data pipelines |
| AI estimate quality | Within 10% of market price on average | Mean absolute deviation between AI estimates and Kalshi prices |
| Test suite | Clean, passing test suite with >80% core coverage | `pytest` passing, coverage report generated |
| Paper trades | 10+ logged trades with complete fields | Trade log contains all required fields for each trade |
| Calibration data | Brier score computed and calibration curve generated | Calibration analysis completed on paper trading data |
| Documentation | Complete and accurate | README, API reference, configuration guide all written |
| Fee model | Validated against real fees | Fee calculator matches actual Kalshi charges within $0.01 |
| CLI functional | All commands working with help text | `kalshi-intel --help` shows all available commands |
| Forward plan | Written and honest | Document stating whether to continue, pivot, or stop |

---

## Risk Factors

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Kalshi API changes** | Medium | High -- breaks client | Pin API version; implement version detection; monitor Kalshi changelog |
| **Rate limit changes** | Low-Medium | Medium -- slows scanning | Implement exponential backoff; cache aggressively; respect published limits |
| **Demo API divergence from production** | Low | Medium -- paper trading results may not match live | Validate key behaviors in demo vs. production; start live trading small |
| **External data source downtime** | Medium | Low -- degrades estimates | Implement fallbacks; cache last-known-good data; alert on stale data |
| **LLM API changes or cost increases** | Medium | Medium -- estimation quality or cost | Abstract LLM provider; support multiple models; cache estimates |

### Regulatory and Market Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Regulatory changes** | Low | High -- may restrict trading or change rules | Monitor CFTC announcements; diversify across categories; see `06_legal_tax.md` |
| **Fee structure changes** | Medium | High -- may eliminate thin edges | Model fees conservatively; only pursue strategies with >5% edge after fees |
| **Market efficiency increases** | High | Medium -- edges erode over time | Continuously search for new categories; monitor early warning indicators |
| **Liquidity drying up** | Medium | Medium -- cannot execute at fair prices | Size positions relative to available liquidity; set limit orders |

### Execution Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Scope creep** | High | Medium -- delays milestones | Stick to weekly goals; defer "nice-to-have" features |
| **Over-engineering** | Medium | Medium -- delays delivery | Build minimum viable version first; iterate |
| **Insufficient testing** | Medium | High -- bugs in production | Write tests as you build; CI enforces test suite |
| **Estimation overconfidence** | High | High -- wrong sizing, losses | Use quarter-Kelly or less; track calibration from Day 1 |

---

## Contingency Plans

| Scenario | Action |
|---|---|
| **API client not working by Day 7** | Simplify scope; use `requests` instead of async; focus on 3 core endpoints |
| **Scanner produces no opportunities** | Expand market categories; loosen filters; verify data pipeline is working |
| **AI estimates are wildly inaccurate** | Iterate on prompts; add more data context; reduce confidence in estimates; extend paper trading |
| **Demo API not available** | Use cached market data for testing; defer paper trading to live with micro-positions |
| **External data sources fail** | Implement graceful degradation; estimate without external data; add sources incrementally |
| **Time budget exceeded** | Prioritize: API client > scanner > CLI > AI estimation > reports; cut reporting last |

---

## Timeline Summary

```
Week 1 (Days 1-7):   FOUNDATION
  Repository + CI + API Client + Fee Calculator + Models + Demo API Testing

Week 2 (Days 8-14):  ANALYSIS
  Kelly Sizing + Market Scanner + Scoring + Hedging + CLI Commands

Week 3 (Days 15-21): INTELLIGENCE
  AI Estimation + FRED/BLS/NOAA Integration + Daily Reports + WebSocket Monitor

Week 4 (Days 22-30): POLISH & DEPLOY
  Calibration Analysis + Trade Logging + P&L + Documentation + Paper Trading
```

---

## Post-30-Day Decision Framework

At Day 30, evaluate results honestly and choose one path:

| Decision | Criteria | Next Step |
|---|---|---|
| **Scale up** | Calibration Brier score < 0.20, positive paper trading P&L after fees, 2+ categories showing edge | Increase capital to $1,000; continue refining |
| **Continue refining** | Mixed results, some categories promising, estimation improving | Same capital; iterate on prompts and data sources for 30 more days |
| **Pivot** | Current categories showing no edge; new categories identified | Shift focus to unexplored market categories |
| **Pause** | Results inconclusive; need more data | Extend paper trading for 30 days; do not add capital |
| **Stop** | No edge found after honest analysis; negative expected value after fees | Document lessons learned; shut down cleanly |

**Bottom line:** The 30-day roadmap is designed to minimize regret. By building systematically, validating with paper trades, and tracking everything, you will either discover a real edge worth scaling or learn that the edge does not exist before losing significant capital. Both outcomes are valuable.
