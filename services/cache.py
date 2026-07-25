"""
Tiny in-memory TTL cache.

Why this exists:
Hypixel's API allows a limited number of requests per 5-minute window per key,
and Mojang's profile lookup endpoint has its own (unpublished, stricter) limits.
The dashboard can have many browser tabs open at once (the client, their staff,
you) all polling the same /api/* endpoints every ~15-20 seconds. Without a
shared server-side cache, every browser refresh would translate into a fresh
upstream request and you would burn through the rate limit in minutes.

This cache sits between our Flask routes and the outside APIs. It is process-
local (not shared across multiple server workers) which is fine for a single
small Flask process; if you ever run this behind gunicorn with more than one
worker, swap this for Redis and keep the same get_or_set() interface.
"""

import time
import threading
from typing import Any, Callable


class TTLCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get_or_set(self, key: str, ttl_seconds: float, producer: Callable[[], Any]) -> Any:
        """Return the cached value for `key` if still fresh, otherwise call
        `producer()` to compute a new value, cache it, and return it.

        If `producer` raises and we have a stale cached value, we return the
        stale value rather than letting the error bubble up -- a dashboard
        showing "last known" numbers for a few extra seconds is much better
        than one that shows an error screen because Hypixel had a hiccup.
        """
        now = time.monotonic()
        with self._lock:
            cached = self._store.get(key)
            if cached is not None and (now - cached[0]) < ttl_seconds:
                return cached[1]

        try:
            value = producer()
        except Exception:
            if cached is not None:
                return cached[1]
            raise

        with self._lock:
            self._store[key] = (now, value)
        return value


cache = TTLCache()
