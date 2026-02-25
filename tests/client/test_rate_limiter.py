"""Tests for rate limiter."""

import pytest

from kalshi_intel.client.rate_limiter import RateLimiter, TokenBucketRateLimiter


class TestTokenBucketRateLimiter:
    def test_acquire_succeeds_when_tokens_available(self):
        limiter = TokenBucketRateLimiter(rate=100)
        limiter.acquire()  # Should not raise

    def test_available_starts_at_burst(self):
        limiter = TokenBucketRateLimiter(rate=10, burst=10)
        assert limiter.available >= 9.0  # close to 10, may tick slightly

    def test_timeout_raises(self):
        limiter = TokenBucketRateLimiter(rate=1, burst=1)
        limiter.acquire()  # Use the one token
        with pytest.raises(TimeoutError):
            limiter.acquire(timeout=0.1)


class TestRateLimiter:
    def test_dual_buckets(self):
        rl = RateLimiter(read_rate=20, write_rate=10)
        rl.acquire_read()  # Should not raise
        rl.acquire_write()  # Should not raise
