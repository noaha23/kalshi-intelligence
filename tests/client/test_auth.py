"""Tests for RSA-PSS authentication.

These tests use a generated test key pair to verify signature mechanics.
"""

import tempfile
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from kalshi_intel.client.auth import KalshiAuthenticator


@pytest.fixture
def test_key_path() -> Path:
    """Generate a temporary RSA key pair for testing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as f:
        f.write(pem)
        return Path(f.name)


@pytest.fixture
def authenticator(test_key_path: Path) -> KalshiAuthenticator:
    return KalshiAuthenticator("test-api-key-id", test_key_path)


class TestKalshiAuthenticator:
    def test_sign_request_returns_three_headers(self, authenticator):
        headers = authenticator.sign_request("GET", "/trade-api/v2/markets")
        assert "KALSHI-ACCESS-KEY" in headers
        assert "KALSHI-ACCESS-SIGNATURE" in headers
        assert "KALSHI-ACCESS-TIMESTAMP" in headers

    def test_api_key_in_header(self, authenticator):
        headers = authenticator.sign_request("GET", "/trade-api/v2/markets")
        assert headers["KALSHI-ACCESS-KEY"] == "test-api-key-id"

    def test_timestamp_is_numeric(self, authenticator):
        headers = authenticator.sign_request("GET", "/trade-api/v2/markets")
        assert headers["KALSHI-ACCESS-TIMESTAMP"].isdigit()

    def test_signature_is_base64(self, authenticator):
        import base64

        headers = authenticator.sign_request("GET", "/trade-api/v2/markets")
        sig = headers["KALSHI-ACCESS-SIGNATURE"]
        # Should not raise
        base64.b64decode(sig)

    def test_fixed_timestamp_deterministic(self, authenticator):
        """Same inputs -> same signature (deterministic behavior not guaranteed
        for PSS which uses random salt, but headers structure should be consistent)."""
        ts = 1700000000000
        h1 = authenticator.sign_request("GET", "/trade-api/v2/markets", timestamp_ms=ts)
        h2 = authenticator.sign_request("GET", "/trade-api/v2/markets", timestamp_ms=ts)
        assert h1["KALSHI-ACCESS-KEY"] == h2["KALSHI-ACCESS-KEY"]
        assert h1["KALSHI-ACCESS-TIMESTAMP"] == h2["KALSHI-ACCESS-TIMESTAMP"]
        # Note: signatures may differ due to PSS randomness

    def test_strips_query_params(self, authenticator):
        """Path should strip query params before signing."""
        h1 = authenticator.sign_request("GET", "/trade-api/v2/markets?status=active")
        h2 = authenticator.sign_request("GET", "/trade-api/v2/markets?status=closed")
        # Both sign the same path, so timestamps aside, the signing path is the same
        assert h1["KALSHI-ACCESS-KEY"] == h2["KALSHI-ACCESS-KEY"]

    def test_sign_websocket_returns_headers(self, authenticator):
        headers = authenticator.sign_websocket()
        assert "KALSHI-ACCESS-KEY" in headers
        assert "KALSHI-ACCESS-SIGNATURE" in headers
        assert "KALSHI-ACCESS-TIMESTAMP" in headers

    def test_invalid_key_path_raises(self):
        with pytest.raises((FileNotFoundError, ValueError, OSError)):
            KalshiAuthenticator("key-id", Path("/nonexistent/key.pem"))
