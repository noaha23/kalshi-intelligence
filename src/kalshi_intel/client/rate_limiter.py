"""Thread-safe token bucket rate limiter for Kalshi API requests."""

import threading
import time


class TokenBucketRateLimiter:
    """Token bucket rate limiter.

    Tokens replenish at a fixed rate. Each request consumes one token.
    If no tokens available, blocks until one is replenished.
    """

    def __init__(self, rate: float, burst: int | None = None) -> None:
        """
        Args:
            rate: Tokens replenished per second.
            burst: Maximum tokens in bucket (defaults to rate).
        """
        self.rate = rate
        self.burst = burst if burst is not None else int(rate)
        self._tokens = float(self.burst)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def acquire(self, tokens: int = 1, timeout: float = 30.0) -> None:
        """Block until tokens are available.

        Raises:
            TimeoutError: If tokens not available within timeout.
        """
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"Rate limiter timeout: could not acquire {tokens} token(s) within {timeout}s"
                )
            # Sleep for estimated time until next token, capped at remaining timeout
            time.sleep(min(1.0 / self.rate, remaining))

    @property
    def available(self) -> float:
        """Current available tokens (approximate)."""
        with self._lock:
            self._refill()
            return self._tokens


class RateLimiter:
    """Dual-bucket limiter: separate read and write limits."""

    def __init__(self, read_rate: int = 20, write_rate: int = 10) -> None:
        self.read = TokenBucketRateLimiter(rate=read_rate)
        self.write = TokenBucketRateLimiter(rate=write_rate)

    def acquire_read(self) -> None:
        self.read.acquire()

    def acquire_write(self) -> None:
        self.write.acquire()
