"""Local disk cache for API responses."""

import hashlib
import json
import time
from pathlib import Path


class DiskCache:
    """Simple file-based cache with TTL expiration.

    Stores JSON-serializable data in the cache directory.
    Each entry is a file named by the hash of the cache key.
    """

    def __init__(self, cache_dir: str = "data/cache", default_ttl: int = 300) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl

    def _key_path(self, key: str) -> Path:
        hashed = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self.cache_dir / f"{hashed}.json"

    def get(self, key: str) -> dict | None:
        """Get cached value if not expired."""
        path = self._key_path(key)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text())
            if time.time() > data.get("_expires_at", 0):
                path.unlink(missing_ok=True)
                return None
            return data.get("value")
        except (json.JSONDecodeError, OSError):
            return None

    def set(self, key: str, value: dict, ttl: int | None = None) -> None:
        """Cache a value with TTL."""
        ttl = ttl if ttl is not None else self.default_ttl
        data = {
            "value": value,
            "_expires_at": time.time() + ttl,
            "_key": key,
        }
        self._key_path(key).write_text(json.dumps(data))

    def clear(self) -> int:
        """Remove all cached entries. Returns count of removed files."""
        count = 0
        for path in self.cache_dir.glob("*.json"):
            path.unlink(missing_ok=True)
            count += 1
        return count
