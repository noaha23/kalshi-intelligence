"""Public data source fetchers for market analysis.

Supported sources:
- FRED (Federal Reserve Economic Data): CPI, unemployment, GDP, interest rates
- NOAA: Weather forecasts and historical temperatures
- CME FedWatch: Interest rate probabilities (placeholder)

All fetchers return DataPoint objects for consistent downstream processing.
"""

from dataclasses import dataclass
from datetime import date


@dataclass
class DataPoint:
    """A single data observation from an external source."""

    source: str
    metric: str
    value: float
    date: date
    unit: str = ""
    url: str = ""


# Registry of data sources by market category
CATEGORY_SOURCES: dict[str, list[dict[str, str]]] = {
    "economics": [
        {"name": "BLS CPI", "url": "https://www.bls.gov/cpi/", "metrics": "CPI, inflation"},
        {
            "name": "BLS Employment",
            "url": "https://www.bls.gov/ces/",
            "metrics": "Jobs, unemployment",
        },
        {"name": "BEA GDP", "url": "https://www.bea.gov/", "metrics": "GDP growth"},
        {
            "name": "FRED",
            "url": "https://fred.stlouisfed.org/",
            "metrics": "All economic indicators",
        },
        {
            "name": "CME FedWatch",
            "url": "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html",
            "metrics": "Fed rate probabilities",
        },
    ],
    "weather": [
        {"name": "NOAA/NWS", "url": "https://www.weather.gov/", "metrics": "Forecasts, temps"},
        {
            "name": "Weather Underground",
            "url": "https://www.wunderground.com/",
            "metrics": "Detailed forecasts",
        },
    ],
    "politics": [
        {
            "name": "FiveThirtyEight",
            "url": "https://projects.fivethirtyeight.com/",
            "metrics": "Polls, models",
        },
        {
            "name": "RealClearPolitics",
            "url": "https://www.realclearpolitics.com/",
            "metrics": "Polling averages",
        },
    ],
    "financials": [
        {
            "name": "Yahoo Finance",
            "url": "https://finance.yahoo.com/",
            "metrics": "Stock prices, indices",
        },
        {"name": "CBOE", "url": "https://www.cboe.com/", "metrics": "VIX, options data"},
    ],
    "crypto": [
        {"name": "CoinGecko", "url": "https://www.coingecko.com/", "metrics": "Crypto prices"},
        {"name": "Binance API", "url": "https://api.binance.com/", "metrics": "Real-time crypto"},
    ],
    "transportation": [
        {
            "name": "TSA",
            "url": "https://www.tsa.gov/travel/passenger-volumes",
            "metrics": "Daily checkpoint numbers",
        },
    ],
    "sports": [
        {"name": "ESPN", "url": "https://www.espn.com/", "metrics": "Scores, stats"},
        {"name": "The Odds API", "url": "https://the-odds-api.com/", "metrics": "Betting odds"},
    ],
}


def get_sources_for_category(category: str) -> list[dict[str, str]]:
    """Return relevant data sources for a market category."""
    key = category.lower().strip()
    for cat_key, sources in CATEGORY_SOURCES.items():
        if cat_key in key or key in cat_key:
            return sources
    return []


def get_sources_for_keywords(text: str) -> list[dict[str, str]]:
    """Match keywords in market rules to data sources."""
    text_lower = text.lower()
    matched = []
    keyword_map = {
        "cpi": "economics",
        "inflation": "economics",
        "unemployment": "economics",
        "jobs": "economics",
        "gdp": "economics",
        "fed": "economics",
        "fomc": "economics",
        "interest rate": "economics",
        "temperature": "weather",
        "weather": "weather",
        "forecast": "weather",
        "hurricane": "weather",
        "s&p": "financials",
        "nasdaq": "financials",
        "bitcoin": "crypto",
        "btc": "crypto",
        "ethereum": "crypto",
        "tsa": "transportation",
        "passenger": "transportation",
        "election": "politics",
        "poll": "politics",
        "president": "politics",
    }

    seen_categories: set[str] = set()
    for keyword, category in keyword_map.items():
        if keyword in text_lower and category not in seen_categories:
            seen_categories.add(category)
            matched.extend(CATEGORY_SOURCES.get(category, []))

    return matched


class FREDFetcher:
    """Federal Reserve Economic Data (FRED) API client.

    Requires a FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html
    """

    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def get_series(
        self,
        series_id: str,
        start_date: date | None = None,
        limit: int = 10,
    ) -> list[DataPoint]:
        """Fetch a FRED data series.

        Common series IDs:
        - CPIAUCSL: CPI for all urban consumers
        - UNRATE: Unemployment rate
        - GDP: Gross domestic product
        - FEDFUNDS: Federal funds rate
        - T10Y2Y: 10-year minus 2-year Treasury spread
        """
        if not self.api_key:
            raise ValueError("FRED API key required. Set FRED_API_KEY in .env")

        import httpx

        params: dict = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit,
        }
        if start_date:
            params["observation_start"] = start_date.isoformat()

        resp = httpx.get(f"{self.BASE_URL}/series/observations", params=params)
        resp.raise_for_status()
        data = resp.json()

        points = []
        for obs in data.get("observations", []):
            try:
                points.append(
                    DataPoint(
                        source="FRED",
                        metric=series_id,
                        value=float(obs["value"]),
                        date=date.fromisoformat(obs["date"]),
                        url=f"https://fred.stlouisfed.org/series/{series_id}",
                    )
                )
            except (ValueError, KeyError):
                continue
        return points
