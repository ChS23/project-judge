import time
from typing import Any

from judge.settings import settings


class TTLCache:
    """In-memory TTL кеш для данных из Google Sheets."""

    def __init__(self, ttl: int | None = None):
        self._store: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl or settings.roster_cache_ttl

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (value, time.time() + self._ttl)

    def clear(self) -> None:
        self._store.clear()


roster_cache = TTLCache()
rubrics_cache = TTLCache()
