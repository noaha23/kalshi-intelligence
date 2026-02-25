# Kalshi Market Intelligence System

Research and analysis tools for Kalshi prediction markets.

> **DISCLAIMER**: This is a research project for educational purposes only. It is not financial advice. Trading prediction market contracts involves risk of loss. All code is provided as-is with no guarantees of accuracy or profitability. Consult a qualified financial advisor before making trading decisions.

## Features

- **API Client**: Full Kalshi REST + WebSocket client with RSA-PSS authentication
- **Market Scanner**: Daily scanning workflow with multi-factor scoring rubric
- **Fee Calculator**: Taker/maker fee calculations for binary contracts
- **Position Sizing**: Kelly criterion with fractional Kelly and exposure caps
- **Hedging Analysis**: Hedge formulas for binary and multivariate contracts
- **AI Probability Estimation**: Claude/GPT-powered probability estimates with structured prompts
- **Trade Logging**: CSV-based trade log with P&L tracking
- **Daily Reports**: Markdown/JSON reports of market opportunities

## Quick Start

```bash
# Install dependencies
uv sync

# Copy and configure environment
cp .env.example .env
# Edit .env with your Kalshi API credentials

# Run CLI
uv run kalshi-intel --help

# Example: calculate fees
uv run kalshi-intel fees 50 --count 10

# Example: position sizing
uv run kalshi-intel position-size 0.65 50 --bankroll 500000

# Example: scan markets
uv run kalshi-intel scan --top-n 10
```

## Setup

1. Create a Kalshi account and generate API keys (Settings > API)
2. Save your private key PEM file to `keys/kalshi_private.pem`
3. Copy `.env.example` to `.env` and fill in your credentials
4. Start with `KALSHI_ENVIRONMENT=demo` for testing

## Project Structure

```
src/kalshi_intel/
  client/       # Kalshi API client (auth, REST, WebSocket)
  scanner/      # Market opportunity scanning & scoring
  analysis/     # Fees, hedging, position sizing, AI estimation
  data/         # External data sources & historical data
  reports/      # Daily reports & trade logging
  utils/        # Shared utilities
docs/           # Workstream documentation (7 documents)
tests/          # Unit & integration tests
```

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
make test

# Lint & format
make lint
make fmt

# Type check
make type-check
```

## Documentation

See the `docs/` directory for detailed workstream documentation:

1. [API Integration](docs/01_api_integration.md)
2. [Market Scanning](docs/02_market_scanning.md)
3. [Hedging Framework](docs/03_hedging_framework.md)
4. [Probability Estimation](docs/04_probability_estimation.md)
5. [Competitive Intelligence](docs/05_competitive_intelligence.md)
6. [Legal & Tax](docs/06_legal_tax.md)
7. [Execution Roadmap](docs/07_execution_roadmap.md)
