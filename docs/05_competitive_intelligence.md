# Competitive Intelligence & Edge Validation

> **Disclaimer:** This document is for educational and research purposes only. It does not constitute financial, investment, or trading advice. Past performance does not guarantee future results. Conduct your own due diligence before trading.

---

## 1. Kalshi Market Landscape

Kalshi is the only CFTC-regulated Designated Contract Market (DCM) for event contracts in the United States. The platform offers binary contracts across a broad range of categories, each with distinct data ecosystems, liquidity profiles, and edge potential.

### Market Categories

| Category | Examples | Typical Liquidity | Data Richness |
|---|---|---|---|
| **Economics** | CPI prints, jobs reports, GDP, Fed rate decisions | Medium-High | Very High |
| **Climate/Weather** | Temperature thresholds, hurricane landfalls, snowfall | Medium | High |
| **Finance** | S&P 500 ranges, VIX levels, earnings outcomes | Medium-High | Very High |
| **Politics** | Election outcomes, approval ratings, policy events | High (seasonal) | Medium |
| **Tech** | Product launches, subscriber milestones, IPO timing | Low | Low-Medium |
| **Sports** | Game outcomes, player props, championship winners | Very High | High |
| **Entertainment** | Box office thresholds, award winners, streaming numbers | Low | Low |
| **Transportation** | TSA throughput, airline passenger counts, flight delays | Low | Medium-High |

### Market Structure

| Attribute | Detail |
|---|---|
| Contract type | Binary (YES or NO outcome) |
| Payout structure | YES + NO always sum to $1.00 |
| Price range | $0.01 to $0.99 per contract |
| Implied probability | Contract price = implied probability (e.g., $0.65 = 65%) |
| Settlement | $1.00 to winning side, $0.00 to losing side |
| Regulation | CFTC-regulated Designated Contract Market (DCM) |
| Margin/leverage | None -- full contract value paid upfront |
| Fee structure | Varies by market; typically $0.01-$0.03 per contract per side |

---

## 2. Key Data Sources by Category

Systematic edge on Kalshi comes from faster, more accurate, or more comprehensive analysis of publicly available data. The following data sources form the foundation of a quantitative approach.

### Economics

| Source | Data | URL / Access | Refresh Frequency |
|---|---|---|---|
| **Bureau of Labor Statistics (BLS)** | CPI, PPI, employment situation, jobless claims | bls.gov/data | Monthly/weekly per series |
| **Bureau of Economic Analysis (BEA)** | GDP (advance, second, third estimates), PCE | bea.gov | Quarterly/monthly |
| **FRED (St. Louis Fed)** | 800,000+ economic time series, aggregated from BLS/BEA/Census | fred.stlouisfed.org | Varies by series |
| **CME FedWatch Tool** | Implied probabilities of Fed rate decisions from futures | cmegroup.com/markets/interest-rates | Real-time (market hours) |
| **Bloomberg Consensus** | Professional forecaster consensus for economic releases | Subscription required | Pre-release |
| **Census Bureau** | Retail sales, housing starts, trade data | census.gov | Monthly |
| **ADP National Employment Report** | Private payroll estimates (pre-BLS) | adpemploymentreport.com | Monthly (2 days before BLS) |

**Edge angle:** BLS and BEA release schedules are published months in advance. Machine-readable data is available within seconds of release. Markets that reference specific BLS/BEA numbers can be evaluated with near-instant data ingestion.

### Climate/Weather

| Source | Data | URL / Access | Refresh Frequency |
|---|---|---|---|
| **NOAA / National Weather Service (NWS)** | Forecasts, historical observations, storm tracking | weather.gov, api.weather.gov | Hourly to daily |
| **NOAA Climate Prediction Center** | Temperature outlooks, precipitation forecasts | cpc.ncep.noaa.gov | Weekly/monthly |
| **ECMWF (European Centre)** | Global ensemble forecasts, considered gold standard | ecmwf.int | Every 6-12 hours |
| **GFS (Global Forecast System)** | NOAA's global weather model | nomads.ncep.noaa.gov | Every 6 hours |
| **Weather Underground** | Historical station data, personal weather stations | wunderground.com | Real-time |
| **NOAA Storm Prediction Center** | Severe weather outlooks, tornado watches | spc.noaa.gov | As needed |

**Edge angle:** NOAA ensemble model data is public but under-utilized by retail participants. Probabilistic forecasts from multiple model runs provide direct probability estimates that can be compared to Kalshi market prices.

### Finance

| Source | Data | URL / Access | Refresh Frequency |
|---|---|---|---|
| **Yahoo Finance** | Stock prices, earnings dates, analyst estimates | finance.yahoo.com | Real-time (delayed 15 min for some) |
| **CBOE VIX** | Implied volatility index | cboe.com | Real-time (market hours) |
| **Federal Reserve** | FOMC minutes, speeches, Beige Book | federalreserve.gov | Per meeting/publication |
| **SEC EDGAR** | Company filings, earnings reports | sec.gov/edgar | As filed |
| **FINRA** | Short interest data | finra.org | Bi-monthly |
| **Options chains** | Implied probability distributions from options markets | Various brokers | Real-time |

**Edge angle:** Options-implied distributions can be directly compared to Kalshi contract prices for financial markets. Divergences between options-implied probabilities and Kalshi prices represent potential opportunities.

### Politics

| Source | Data | URL / Access | Refresh Frequency |
|---|---|---|---|
| **FiveThirtyEight** | Polling averages, election forecasts, model outputs | fivethirtyeight.com (now at ABC) | Daily during election cycles |
| **RealClearPolitics** | Polling aggregation, averages | realclearpolitics.com | Daily |
| **Gallup** | Presidential approval, consumer confidence | gallup.com | Weekly/monthly |
| **Cook Political Report** | Race ratings, political analysis | cookpolitical.com | As updated |
| **State election boards** | Official results, voter registration data | Varies by state | Per election cycle |

**Edge angle:** Polling aggregation models provide probability estimates that can be compared to Kalshi prices. Political markets are heavily traded around elections but often mispriced in off-cycle periods.

### Transportation

| Source | Data | URL / Access | Refresh Frequency |
|---|---|---|---|
| **TSA Checkpoint Data** | Daily passenger throughput numbers | tsa.gov/travel/passenger-volumes | Daily (next-day publication) |
| **FAA** | Air traffic data, delay statistics | faa.gov | Daily |
| **Bureau of Transportation Statistics** | Airline on-time performance, passenger counts | bts.gov | Monthly |
| **FlightAware / FlightRadar24** | Real-time flight tracking | flightaware.com | Real-time |

**Edge angle:** TSA data is published with a one-day lag and follows strong seasonal and day-of-week patterns. Historical data enables robust statistical modeling for throughput-based contracts.

### Sports

| Source | Data | URL / Access | Refresh Frequency |
|---|---|---|---|
| **ESPN** | Scores, schedules, player stats, injury reports | espn.com | Real-time |
| **Odds aggregators** | Consensus lines from sportsbooks | oddschecker.com, vegasinsider.com | Real-time |
| **Team/league official sites** | Injury reports, roster moves | Varies | As updated |
| **Sports Reference** | Historical statistics databases | sports-reference.com | Daily |

**Edge angle:** Sports markets on Kalshi are heavily competed and represent 89% of platform revenue. Edge is hardest to find here due to sophisticated market makers and deep liquidity. Most systematic edge has already been arbitraged away.

---

## 3. Existing Tools and Competitors

### Kalshi Official SDKs and Libraries

| Tool | Type | Language | Notes |
|---|---|---|---|
| `kalshi-python` (sync) | Official SDK | Python | REST API wrapper, synchronous |
| `kalshi-python` (async) | Official SDK | Python | Async variant for concurrent operations |
| Kalshi REST API | Direct API | Any (HTTP) | Full market data, order management, account info |
| Kalshi WebSocket | Real-time feed | Any (WS) | Order book updates, trade feed |
| Kalshi FIX Protocol | Institutional | FIX 4.4 | Low-latency, for market makers |

### Competing Platforms

| Platform | Regulation | Settlement | Key Difference from Kalshi |
|---|---|---|---|
| **Polymarket** | None (offshore) | Crypto (USDC) | Higher liquidity in political markets; not legal for US residents |
| **Metaculus** | N/A | No real money | Forecasting-only; useful for calibration comparison |
| **PredictIt** | CFTC no-action (revoked) | USD | Winding down; historically the main US prediction market |
| **Iowa Electronic Markets** | CFTC no-action | USD | Academic, tiny scale, limited markets |
| **Manifold Markets** | N/A | Play money | Community-driven; useful for sentiment data |

### Known Open-Source Trading Bots

Multiple open-source projects targeting Kalshi exist on GitHub:

| Project Type | Approach | Observed Performance |
|---|---|---|
| Weather bots | NOAA data ingestion, probabilistic models | Marginal (Chris Dodds reported barely breaking even) |
| TSA checkpoint bots | Historical throughput data | Limited by low liquidity (Ferraiolo case study) |
| Market makers | Spread-based quoting on multiple markets | Unknown P&L; several repos exist |
| AI/LLM bots | GPT-based probability estimation | Experimental; no published track records |
| Arbitrage bots | Cross-platform price comparison | Limited by Kalshi-only USD settlement |

### Prediction Market Aggregators

| Aggregator | Coverage | Use Case |
|---|---|---|
| Metaculus | Broad (science, tech, geopolitics) | Calibration benchmarking |
| Elicit / Manifold | Community forecasts | Sentiment comparison |
| Polymarket (read-only) | Politics, crypto, culture | Cross-platform price comparison |
| CFTC commitment data | Kalshi position reporting | Market structure analysis |

---

## 4. Edge Identification Framework

The core thesis for systematic trading on Kalshi: find markets where publicly available data implies a different probability than the current market price, after accounting for fees and uncertainty.

### Edge Formula

```
Estimated Edge = |Your Probability - Market Price| - Round-Trip Fees - Uncertainty Margin
```

An opportunity exists when Estimated Edge > 0.

### Step-by-Step Edge Identification Process

1. **Scan markets** -- Identify active contracts with sufficient liquidity (bid-ask spread, open interest).
2. **Gather data** -- Pull relevant public data for the contract's underlying event.
3. **Estimate probability** -- Use quantitative models, AI-assisted analysis, or structured reasoning to generate a probability estimate.
4. **Compare to market** -- Calculate the difference between your estimate and the market's implied probability.
5. **Account for fees** -- Subtract round-trip trading fees (entry + exit or entry + settlement).
6. **Assess uncertainty** -- Discount your edge by your confidence level in the estimate.
7. **Size position** -- Use fractional Kelly criterion to determine position size.
8. **Execute or pass** -- Only trade when net expected edge exceeds your minimum threshold (recommended: 5% after fees).

### Where Edge Is Most Likely

| Condition | Why It Creates Edge |
|---|---|
| Low retail attention | Fewer participants = less efficient pricing |
| Structured public data available | Quantitative models can outperform gut-feel pricing |
| Short time to resolution | Less time for market to self-correct |
| Event-specific domain expertise | Specialized knowledge not reflected in price |
| Data released on a schedule | Enables pre-positioning based on data pipeline speed |
| Thin order books | Small trades can move price; wide spreads contain opportunity |

### Where Edge Is Least Likely

| Condition | Why |
|---|---|
| High-liquidity sports markets | Sophisticated market makers with deep domain expertise |
| Headline political events | Heavy media coverage = efficient pricing |
| Markets closely tracked by professional forecasters | Consensus already priced in |
| Long-duration contracts with no new information | Price reflects all known information |

---

## 5. Validation Approaches

### Historical Calibration Analysis

Test whether your estimation approach would have been accurate on past markets:

1. **Collect historical Kalshi data** -- Past market prices and settlement outcomes.
2. **Apply your model retroactively** -- Generate probability estimates for historical contracts using data available at the time.
3. **Compute calibration metrics**:
   - **Brier Score**: Mean squared error between estimates and outcomes (lower = better, 0.25 = random).
   - **Calibration curve**: Plot estimated probabilities vs. actual frequencies (diagonal = perfectly calibrated).
   - **Resolution**: How much your estimates vary from the base rate (higher = more informative).
4. **Compare to market** -- Is your model better calibrated than the market price itself?

| Calibration Metric | Good | Acceptable | Poor |
|---|---|---|---|
| Brier Score | < 0.15 | 0.15 - 0.25 | > 0.25 |
| Mean absolute error | < 5% | 5% - 15% | > 15% |
| Overconfidence rate | < 10% | 10% - 25% | > 25% |

### Cross-Platform Comparison

Compare Kalshi prices to probability estimates from other sources:

| Comparison Source | What It Tells You |
|---|---|
| Polymarket (same or similar contract) | Direct cross-platform price arbitrage signal |
| Metaculus community median | Whether crowd wisdom diverges from Kalshi price |
| Professional forecaster consensus (Bloomberg, Survey of Professional Forecasters) | Whether experts agree with the market |
| Options-implied probabilities | For financial contracts, options markets may be more liquid/efficient |
| Your own model | Whether your quantitative estimate diverges meaningfully |

**A divergence is not automatically an edge.** It may mean: (a) you have better information, (b) the other source has better information, (c) structural differences between platforms explain the gap, or (d) the comparison is not apples-to-apples.

### Data Freshness Advantages

For markets tied to scheduled data releases, speed of data ingestion can be a source of edge:

| Data Release | Source | Typical Release Time | Kalshi Reaction Window |
|---|---|---|---|
| CPI report | BLS | 8:30 AM ET (monthly) | Seconds to minutes |
| Employment situation | BLS | 8:30 AM ET (monthly) | Seconds to minutes |
| GDP estimate | BEA | 8:30 AM ET (quarterly) | Seconds to minutes |
| FOMC decision | Federal Reserve | 2:00 PM ET (per meeting) | Seconds |
| Weather forecast update | NOAA/NWS | Multiple times daily | Minutes to hours |
| TSA throughput | TSA | Next-day publication | Hours |

**Implementation:** Build automated data ingestion pipelines that pull structured data from BLS, BEA, NOAA, and TSA APIs as soon as they publish. Parse the data, run it through your probability model, and compare to current Kalshi prices. If a meaningful discrepancy exists and the market has not yet adjusted, that is the window of opportunity.

**Realistic caveat:** For high-profile releases (CPI, jobs), market makers with low-latency connections will adjust prices within seconds. Edge from data speed alone is unlikely for headline numbers. The advantage is stronger for niche releases, secondary data points, and markets with lower institutional attention.

---

## 6. Early Warning Indicators for Edge Erosion

Monitor these signals to detect when an edge is degrading:

- Bid-ask spreads narrowing in target markets (more market makers entering)
- Win rate declining over a 30-trade rolling window
- New GitHub repos or blog posts describing your strategy's approach
- Kalshi announcements about institutional partnerships in your market category
- Volume increasing in previously low-liquidity markets without corresponding price inefficiency
- Orders getting filled at worse prices consistently (increased competition)
- Fee structure changes announced by Kalshi

---

## 7. Actionable Next Steps

### Immediate

- Catalog all public Kalshi trading bots on GitHub; note their strategies and target markets.
- Identify 3-5 niche market categories with low systematic competition.
- Pull current bid-ask spread data for target markets to baseline liquidity.
- Set up data ingestion for at least one source per target category (NOAA, BLS, TSA).

### Short-Term (Weeks 2-4)

- Build a competitive monitoring process: track new GitHub repos, blog posts, and Kalshi announcements.
- Quantify fee impact on target strategies using the fee calculator module.
- Test data pipelines for NOAA weather and BLS economic data.
- Run historical calibration analysis on at least one market category.

### Ongoing

- Review early warning indicators weekly.
- Re-evaluate edge thesis monthly based on actual trading results.
- Track Kalshi regulatory filings and CFTC announcements quarterly.
- Maintain a competitive intelligence log with timestamps.

---

## 8. Risks & Considerations

| Risk | Mitigation |
|---|---|
| Edge may not exist in chosen markets | Start with paper trading; validate before committing capital |
| Public bots reveal your strategy space | Differentiate through data sources, not just model architecture |
| Fee changes eliminate thin edges | Model fees conservatively; only pursue strategies with >5% edge after fees |
| Regulatory environment shifts | Monitor CFTC docket; diversify across market categories |
| Low liquidity prevents scaling | Size positions appropriately; accept that some edges are capacity-constrained |
| Overfitting to historical data | Use out-of-sample validation; track live performance vs. backtest |
| Market efficiency increases over time | Plan for edge decay; continuously search for new market categories |

**Bottom line:** Kalshi's regulated status and growing market make it the best US venue for systematic event trading. Edges are thin, fees are real, and competition is increasing. Success requires disciplined edge measurement, conservative sizing, continuous monitoring of the competitive landscape, and a willingness to accept when no edge exists.
