"""RSA-PSS SHA-256 authentication for Kalshi API requests."""

import base64
import datetime
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey


class KalshiAuthenticator:
    """Generates RSA-PSS SHA-256 signatures for Kalshi API requests.

    Signature message format: "{timestamp_ms}{HTTP_METHOD}{path_without_query}"
    Uses PKCS#1 PSS padding with SHA-256, salt_length = digest size (32 bytes).
    """

    def __init__(self, api_key_id: str, private_key_path: Path) -> None:
        self.api_key_id = api_key_id
        self._private_key = self._load_key(private_key_path)

    @staticmethod
    def _load_key(key_path: Path) -> RSAPrivateKey:
        with open(key_path, "rb") as f:
            key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend(),
            )
        if not isinstance(key, RSAPrivateKey):
            raise ValueError(f"Expected RSA private key, got {type(key).__name__}")
        return key

    def _current_timestamp_ms(self) -> int:
        return int(datetime.datetime.now(datetime.UTC).timestamp() * 1000)

    def _sign(self, message: str) -> str:
        """Sign a message with RSA-PSS SHA-256 and return base64-encoded signature."""
        signature = self._private_key.sign(
            message.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("utf-8")

    def sign_request(
        self,
        method: str,
        path: str,
        timestamp_ms: int | None = None,
    ) -> dict[str, str]:
        """Generate authentication headers for a REST API request.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            path: Request path (e.g., "/trade-api/v2/markets"). Query params are stripped.
            timestamp_ms: Override timestamp for testing. Uses current time if None.

        Returns:
            Dict with KALSHI-ACCESS-KEY, KALSHI-ACCESS-SIGNATURE, KALSHI-ACCESS-TIMESTAMP.
        """
        if timestamp_ms is None:
            timestamp_ms = self._current_timestamp_ms()

        path_without_query = path.split("?")[0]
        message = f"{timestamp_ms}{method.upper()}{path_without_query}"
        signature = self._sign(message)

        return {
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": str(timestamp_ms),
        }

    def sign_websocket(self, timestamp_ms: int | None = None) -> dict[str, str]:
        """Generate auth headers for WebSocket handshake.

        Message format: "{timestamp_ms}GET/trade-api/ws/v2"
        """
        if timestamp_ms is None:
            timestamp_ms = self._current_timestamp_ms()

        message = f"{timestamp_ms}GET/trade-api/ws/v2"
        signature = self._sign(message)

        return {
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": str(timestamp_ms),
        }
