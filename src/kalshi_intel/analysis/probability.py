"""AI-assisted probability estimation for Kalshi markets.

DISCLAIMER: This is a research tool. Estimates are for analysis purposes only.
Not financial advice. Always verify with multiple sources.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from kalshi_intel.client.models import Market

logger = logging.getLogger(__name__)


@dataclass
class ProbabilityEstimate:
    """AI-generated probability estimate with reasoning."""

    market_ticker: str
    estimated_probability: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    reasoning: str
    key_factors: list[str] = field(default_factory=list)
    data_gaps: list[str] = field(default_factory=list)
    model_used: str = ""
    edge_vs_market: float = 0.0
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()


class ProbabilityEstimator:
    """Uses LLM APIs to generate probability estimates for Kalshi markets.

    Supports Anthropic Claude and OpenAI GPT models.
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.provider = provider
        self.api_key = api_key

        if provider == "anthropic":
            self.model = model or "claude-sonnet-4-20250514"
        elif provider == "openai":
            self.model = model or "gpt-4o"
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'anthropic' or 'openai'.")

    def estimate(
        self,
        market: Market,
        context: str | None = None,
        reference_data: dict | None = None,
    ) -> ProbabilityEstimate:
        """Generate a probability estimate for a market.

        Args:
            market: The market to analyze.
            context: Additional context (news, data) as text.
            reference_data: Structured data dict to include in prompt.

        Returns:
            ProbabilityEstimate with probability, reasoning, and metadata.
        """
        from kalshi_intel.analysis.prompts.market_analysis import (
            PROBABILITY_ESTIMATION_SYSTEM,
            PROBABILITY_ESTIMATION_USER,
        )
        from kalshi_intel.analysis.prompts.probability_est import (
            build_context_section,
            build_reference_data_section,
        )

        # Calculate days to close
        days_to_close = "unknown"
        if market.close_time:
            close = market.close_time
            if close.tzinfo is None:
                close = close.replace(tzinfo=UTC)
            delta = close - datetime.now(UTC)
            days_to_close = str(max(0, delta.days))

        yes_price = market.yes_ask if market.yes_ask else market.last_price
        no_price = 100 - yes_price if yes_price else 50

        user_prompt = PROBABILITY_ESTIMATION_USER.format(
            market_ticker=market.ticker,
            rules_primary=market.rules_primary or market.title or market.ticker,
            yes_price=yes_price,
            implied_prob=yes_price / 100.0 if yes_price else 0.5,
            no_price=no_price,
            volume_24h=market.volume_24h,
            open_interest=market.open_interest,
            close_time=market.close_time or "unknown",
            days_to_close=days_to_close,
            context_section=build_context_section(context),
            reference_data_section=build_reference_data_section(reference_data),
        )

        # Call the AI provider
        response_text = self._call_llm(PROBABILITY_ESTIMATION_SYSTEM, user_prompt)

        # Parse JSON response
        return self._parse_response(response_text, market)

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM API and return the response text."""
        if self.provider == "anthropic":
            return self._call_anthropic(system_prompt, user_prompt)
        elif self.provider == "openai":
            return self._call_openai(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Call Anthropic Claude API."""
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)
        message = client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI GPT API."""
        import openai

        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""

    def _parse_response(self, response_text: str, market: Market) -> ProbabilityEstimate:
        """Parse LLM response into ProbabilityEstimate."""
        # Try to extract JSON from response
        try:
            # Handle responses that wrap JSON in markdown code blocks
            text = response_text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            data = json.loads(text)
            probability = float(data.get("probability", 0.5))
            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning", "")
            key_factors = data.get("key_factors", [])
            data_gaps = data.get("data_gaps", [])
        except (json.JSONDecodeError, ValueError, IndexError):
            logger.warning("Could not parse JSON from LLM response, using raw text")
            probability = 0.5
            confidence = 0.3
            reasoning = response_text
            key_factors = []
            data_gaps = ["Could not parse structured response"]

        # Calculate edge vs market
        implied = market.mid_price_cents / 100.0 if market.mid_price_cents else 0.5
        edge = probability - implied

        return ProbabilityEstimate(
            market_ticker=market.ticker,
            estimated_probability=probability,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=key_factors,
            data_gaps=data_gaps,
            model_used=self.model,
            edge_vs_market=edge,
        )

    def batch_estimate(self, markets: list[Market]) -> list[ProbabilityEstimate]:
        """Estimate probabilities for multiple markets sequentially."""
        results = []
        for market in markets:
            try:
                est = self.estimate(market)
                results.append(est)
            except Exception as e:
                logger.error(f"Failed to estimate {market.ticker}: {e}")
                results.append(
                    ProbabilityEstimate(
                        market_ticker=market.ticker,
                        estimated_probability=0.5,
                        confidence=0.0,
                        reasoning=f"Estimation failed: {e}",
                        model_used=self.model,
                    )
                )
        return results
