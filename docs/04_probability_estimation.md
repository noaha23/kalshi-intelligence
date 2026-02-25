# AI-Assisted Probability Estimation

> **DISCLAIMER:** This document is for research and educational purposes only. It does not constitute financial, legal, or tax advice. AI-generated probability estimates are imperfect and should never be the sole basis for trading decisions. Trading prediction market contracts involves risk of loss. Consult qualified professionals before making trading decisions.

---

## Overview

The AI-assisted probability estimation pipeline generates calibrated probability estimates for Kalshi prediction markets. The system uses a two-stage prompting approach (research, then estimation) with structured JSON output, supports both Anthropic Claude and OpenAI GPT models, and includes a sanity-check protocol to catch common calibration failures. Estimates are tools for analysis, not trading signals -- they should always be cross-referenced with market prices, external data sources, and historical base rates.

---

## Architecture

### ProbabilityEstimator Class

The `ProbabilityEstimator` class (`src/kalshi_intel/analysis/probability.py`) is the primary interface. It supports both Anthropic and OpenAI providers:

```python
from kalshi_intel.analysis.probability import ProbabilityEstimator

# Default: Claude Sonnet (fast, cost-effective)
estimator = ProbabilityEstimator(provider="anthropic")

# Claude Opus for deep analysis on high-conviction opportunities
estimator = ProbabilityEstimator(provider="anthropic", model="claude-opus-4-0-20250514")

# GPT-4o as an alternative
estimator = ProbabilityEstimator(provider="openai", model="gpt-4o")
```

### Model Selection

| Model | Speed | Reasoning Depth | Cost | Best For |
|-------|-------|----------------|------|----------|
| Claude Sonnet | Fast | Good | Low | Daily scanning, batch estimates |
| Claude Opus | Slow | Excellent | High | Complex multi-factor events, nuanced reasoning |
| GPT-4o | Medium | Good | Medium | Alternative when Anthropic is unavailable, speed-sensitive tasks |

Claude is recommended for nuanced reasoning about multi-factor events. GPT is a viable alternative when speed is prioritized or as a cross-check.

---

## Two-Stage Prompting Pipeline

### Stage 1: Research

Gather and summarize all relevant public data before forming a probability estimate. This grounding step prevents the model from jumping to conclusions.

The research prompt instructs the model to find:
1. Recent news and developments
2. Historical precedents and base rates
3. Expert opinions and consensus forecasts
4. Quantitative data from official sources
5. Key uncertainties and unknowns

### Stage 2: Probability Estimation

Generate a calibrated probability with structured reasoning, informed by the research stage.

The estimation prompt provides market context (current price, volume, time to close) and asks for structured JSON output.

Two-stage prompting produces more calibrated results than single-prompt estimation because the model grounds itself in factual data before generating a number.

---

## Structured Prompt Engineering

### Prompt Templates

All prompt templates are in `src/kalshi_intel/analysis/prompts/`:

| Template | File | Purpose |
|----------|------|---------|
| `PROBABILITY_ESTIMATION_SYSTEM` | `market_analysis.py` | System prompt for the estimation stage |
| `PROBABILITY_ESTIMATION_USER` | `market_analysis.py` | User prompt with injected market data |
| `MARKET_RESEARCH_SYSTEM` | `market_analysis.py` | System prompt for the research stage |
| `MARKET_RESEARCH_USER` | `market_analysis.py` | User prompt for research |
| `SANITY_CHECK_SYSTEM` | `market_analysis.py` | System prompt for calibration review |
| `SANITY_CHECK_USER` | `market_analysis.py` | User prompt for sanity check |
| `build_context_section()` | `probability_est.py` | Format additional context into prompt |
| `build_reference_data_section()` | `probability_est.py` | Format structured data into prompt |

### System Prompt: Probability Estimation

```python
PROBABILITY_ESTIMATION_SYSTEM = """You are a quantitative analyst specializing
in prediction markets. Your task is to estimate the probability of an event
based on available data.

Rules:
- Output a calibrated probability between 0 and 1
- Provide detailed reasoning for your estimate
- List key factors that influence your estimate
- State your confidence level
- Note any data gaps that would improve your estimate
- NEVER provide trading advice or recommendations
- Be explicit about uncertainty and limitations

Format your response as JSON:
{
  "probability": 0.XX,
  "confidence": 0.XX,
  "reasoning": "...",
  "key_factors": ["...", "..."],
  "data_gaps": ["...", "..."]
}"""
```

### System Prompt: Market Research

```python
MARKET_RESEARCH_SYSTEM = """You are a research analyst gathering information
about a prediction market event. Your goal is to find and summarize all
relevant public data that could inform a probability estimate.

Focus on:
1. Recent news and developments
2. Historical precedents and base rates
3. Expert opinions and consensus forecasts
4. Quantitative data from official sources
5. Key uncertainties and unknowns

Be factual and cite sources where possible. Do not provide trading recommendations."""
```

### System Prompt: Sanity Check

```python
SANITY_CHECK_SYSTEM = """You are a calibration reviewer for probability estimates
on prediction markets. Given a probability estimate and the reasoning behind it,
evaluate whether the estimate seems well-calibrated.

Check for:
1. Base rate neglect (is the estimate anchored to historical frequencies?)
2. Availability bias (is the estimate overly influenced by recent events?)
3. Overconfidence (is the confidence interval too narrow?)
4. Conjunction fallacy (does the estimate require multiple independent events?)
5. Missing information (what data gaps could change the estimate?)

Provide a calibration assessment: WELL_CALIBRATED, SLIGHTLY_HIGH, SLIGHTLY_LOW,
SIGNIFICANTLY_HIGH, SIGNIFICANTLY_LOW, or UNCERTAIN."""
```

---

## Context Building

### Market Data Injection

The user prompt template injects live market data into every estimation call:

```python
PROBABILITY_ESTIMATION_USER = """Analyze this prediction market contract:

**Market:** {market_ticker}
**Question:** {rules_primary}
**Current YES price:** {yes_price}c (implied probability: {implied_prob:.1%})
**Current NO price:** {no_price}c
**Volume (24h):** {volume_24h} contracts
**Open Interest:** {open_interest} contracts
**Closes:** {close_time}
**Days until close:** {days_to_close}

{context_section}
{reference_data_section}

Based on all available information, what is your estimated probability
that this market resolves YES?"""
```

Key context fields provided to the model:
- Market ticker and question text
- Current YES/NO prices and implied probability
- Close time and days remaining
- 24h volume and open interest
- Optional free-text context
- Optional structured reference data

### Providing Additional Context

Estimation quality improves significantly with external data:

```python
# Free-text context
est = estimator.estimate(
    market,
    context="BLS released March CPI at 3.8%, above consensus of 3.6%. "
            "Core CPI was 3.4%, in line with expectations."
)

# Structured reference data
est = estimator.estimate(
    market,
    reference_data={
        "Current CPI (Feb)": "3.5%",
        "CPI 3-month trend": "3.2% -> 3.4% -> 3.5%",
        "Cleveland Fed CPI Nowcast": "3.7%",
        "Consensus forecast": "3.6%",
        "Housing CPI component": "5.2% YoY",
    }
)
```

---

## Output Parsing

### ProbabilityEstimate Dataclass

The structured output from each estimation:

```python
@dataclass
class ProbabilityEstimate:
    market_ticker: str
    estimated_probability: float  # 0.0 to 1.0
    confidence: float             # 0.0 to 1.0
    reasoning: str
    key_factors: list[str]
    data_gaps: list[str]
    model_used: str
    edge_vs_market: float         # estimate - implied probability
    timestamp: str                # ISO format UTC
```

### Expected JSON From the LLM

```json
{
  "probability": 0.62,
  "confidence": 0.70,
  "reasoning": "Historical CPI data shows a consistent upward trend over the past 3 months. The latest BLS preliminary indicators suggest continued pressure from housing and energy costs. However, the Fed's rate stance introduces uncertainty.",
  "key_factors": [
    "CPI has exceeded 3.5% in 4 of the last 6 months",
    "Housing component remains elevated at 5.2% YoY",
    "Energy prices declined 2% last month (downward pressure)",
    "Fed held rates, suggesting they see persistent inflation"
  ],
  "data_gaps": [
    "No access to real-time BLS preliminary data",
    "Cannot verify latest energy futures prices",
    "Import price data not yet available for this month"
  ]
}
```

### Edge Calculation

The edge is the difference between the AI estimate and the market's implied probability:

```
edge = estimated_probability - implied_probability
```

Where `implied_probability = yes_price_cents / 100.0`.

A positive edge on YES means the model believes the market underprices the event. A negative edge means the market overprices it (bet NO).

---

## Calibration Considerations

### Common Biases

#### Base Rate Neglect

**Problem:** The model (and humans) often ignore how frequently an event occurs historically.

**Example:** "Will the S&P 500 drop more than 5% this month?"
- Base rate: The S&P drops 5%+ in roughly 3-5% of months historically.
- AI might overweight recent volatility and estimate 15%.
- Always ask: "How often has this happened in the past 20 years?"

**Mitigation:** Include historical base rate data in the `reference_data` parameter.

#### Availability Bias

**Problem:** Recent or vivid events are overweighted.

**Example:** After a major hurricane, the model might overestimate the probability of another hurricane in the same season, even if climatological data says otherwise.

**Mitigation:** Force the model to cite base rates by providing historical data.

#### Overconfidence

**Problem:** AI models tend to express higher confidence than warranted, especially on topics where they have limited training data.

**Mitigation:** Treat the confidence score as directional, not precise. A confidence of 0.8 from the model might correspond to actual calibration of 0.6.

#### Anchoring to Market Price

**Problem:** The prompt includes the current market price. The model may anchor to it rather than reasoning independently.

**Mitigation:** Some practitioners run estimation twice -- once with the market price visible and once without -- and compare. Large differences indicate anchoring.

#### Stale Knowledge

**Problem:** The model's training data has a cutoff date. It cannot access real-time data unless provided.

**Mitigation:** Always provide current data in `context` or `reference_data`. The model's role is to synthesize and reason about data you provide, not to independently know current statistics.

---

## Sanity Check Protocol

After generating an estimate, run it through the calibration review to catch biases:

| Check | Question | Action if Failed |
|-------|----------|------------------|
| Market comparison | Does the estimate differ from market price by > 15%? | Re-examine reasoning |
| Base rate | What is the historical frequency of this event? | Anchor to base rate |
| Other markets | What do Polymarket, Metaculus, or PredictIt say? | Average across platforms |
| Expert consensus | What do subject-matter experts forecast? | Weight expert views |
| Data freshness | Does the model have access to the latest data? | Provide as context |

### When to Override AI Estimates

Override the AI estimate when ANY of these conditions hold:

| Condition | Reason | Action |
|-----------|--------|--------|
| Confidence < 0.5 | Model is not sure | Use market price instead |
| Edge > 5% AND confidence < 0.6 | Large edge with low confidence | Reduce position or skip |
| Contradicts 2+ data sources | Model may lack latest data | Use data source consensus |
| Market moved 10%+ since estimate | Estimate is stale | Re-run estimation |
| Model hallucinated a data point | Reasoning cites non-existent statistics | Discard estimate entirely |
| Edge > 20% | Suspiciously large | Almost certainly miscalibrated |

---

## Batch Estimation for Daily Reports

For daily scanning, estimate probabilities for multiple markets in sequence:

```python
estimator = ProbabilityEstimator(provider="anthropic")
markets = [scanner_result.market for scanner_result in top_scored[:5]]

estimates = estimator.batch_estimate(markets)
for est in estimates:
    print(f"{est.market_ticker}: {est.estimated_probability:.1%} "
          f"(edge: {est.edge_vs_market:+.1%}, conf: {est.confidence:.0%})")
```

**Performance note:** Batch estimation is sequential (one API call per market). For 5 markets with Claude Sonnet, expect approximately 15-30 seconds total.

### Full Report with AI Estimates

```bash
# Generate report with AI estimates for top markets
kalshi-intel report --with-ai --top-n 15 --provider anthropic
```

This runs the scanner, calls `batch_estimate()` on the top results, and saves a combined report with scores, estimates, and edge calculations.

---

## Integration with Scanner

The estimation output feeds directly into the position sizing module:

```python
from kalshi_intel.analysis.probability import ProbabilityEstimator
from kalshi_intel.analysis.position_sizing import calculate_position_size

# Get estimate
est = estimator.estimate(market)

# Only act on high-confidence estimates with meaningful edge
if est.confidence >= 0.6 and abs(est.edge_vs_market) >= 0.05:
    sizing = calculate_position_size(
        true_probability=est.estimated_probability,
        market_price_cents=market.yes_ask,
        bankroll_cents=100_000,
    )
    print(f"Recommended: {sizing.side} {sizing.recommended_contracts} contracts "
          f"@ {sizing.price_cents}c (EV: {sizing.expected_value_cents:.1f}c)")
else:
    print("Insufficient edge or confidence -- skipping")
```

The pipeline flow is: Scanner (identify opportunities) -> Estimator (assess probability) -> Position Sizer (determine bet size) -> Hedger (manage risk after entry).

---

## Calibration Tracking

### Recording Estimates

Track every estimate by recording:

1. Market ticker
2. Estimated probability
3. Market price at time of estimate
4. Confidence level
5. Eventual outcome (YES or NO)

### Bucket Analysis (after 50+ estimates)

Group estimates into buckets. The actual resolution rate should approximately match the bucket midpoint:

| Bucket | Count | Resolved YES | Actual Rate | Expected |
|--------|-------|-------------|-------------|----------|
| 0-20% | 12 | 2 | 17% | 10% |
| 20-40% | 18 | 6 | 33% | 30% |
| 40-60% | 25 | 13 | 52% | 50% |
| 60-80% | 20 | 14 | 70% | 70% |
| 80-100% | 15 | 13 | 87% | 90% |

### Brier Score

Overall calibration metric: `Brier = mean((probability - outcome)^2)` where outcome is 0 or 1. Lower is better. A Brier score of 0.25 is equivalent to always guessing 50%. Anything below 0.20 suggests meaningful skill.

---

## CLI Usage

```bash
# Default estimate (Claude Sonnet)
kalshi-intel estimate ECON-CPI-25MAR

# With additional context
kalshi-intel estimate ECON-CPI-25MAR --context "BLS released preliminary data showing housing costs up 5.2%"

# Using OpenAI
kalshi-intel estimate ECON-CPI-25MAR --provider openai

# Batch estimate top scanner results
kalshi-intel report --with-ai --top-n 15 --provider anthropic
```

---

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `KALSHI_ANTHROPIC_API_KEY` | Anthropic API key for Claude models | (required if using Anthropic) |
| `KALSHI_OPENAI_API_KEY` | OpenAI API key for GPT models | (required if using OpenAI) |

### Cost Estimates

| Model | Per Estimate | 15 Markets Daily | Monthly (30 days) |
|-------|-------------|-----------------|-------------------|
| Claude Sonnet | ~$0.003-0.01 | ~$0.05-0.15 | ~$1.50-4.50 |
| Claude Opus | ~$0.05-0.15 | ~$0.75-2.25 | ~$22.50-67.50 |
| GPT-4o | ~$0.01-0.05 | ~$0.15-0.75 | ~$4.50-22.50 |

---

## Risks and Considerations

- **AI hallucination.** Language models can fabricate statistics, cite non-existent studies, or misremember historical data. Always verify specific factual claims in the reasoning field.
- **Training data cutoff.** Models do not have access to real-time data. For time-sensitive markets, the estimate is only as good as the context you provide.
- **Anchoring to market price.** Including the current market price in the prompt may cause the model to anchor near the market price rather than reasoning independently.
- **Overconfidence in LLM outputs.** AI confidence scores are not well-calibrated. Treat confidence as a relative signal, not an absolute measure.
- **Cost.** Each estimation call costs API credits. Monitor usage for batch operations.
- **Not a crystal ball.** The system synthesizes publicly available information. It does not have access to private data, insider information, or real-time market microstructure.
- **Legal considerations.** Using AI for trading decisions does not exempt you from any applicable regulations. You remain fully responsible for all trading decisions and their consequences.
- **Model degradation.** AI model capabilities and behaviors change with updates. A pipeline that is well-calibrated today may drift over time. Continuously monitor calibration metrics.
- **This is a research tool, not financial advice.** All probability estimates are for informational and educational purposes only. Do not trade based solely on AI-generated probabilities.
