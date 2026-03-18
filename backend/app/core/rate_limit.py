"""
WebGuard RF - Simple in-memory rate limiter
"""

import time
from collections import defaultdict
from threading import Lock

_lock = Lock()
_requests: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(key: str, limit: int = 100, window_sec: float = 60) -> bool:
    """Return True if request allowed, False if rate limited."""
    now = time.time()
    with _lock:
        window_start = now - window_sec
        _requests[key] = [t for t in _requests[key] if t > window_start]
        if len(_requests[key]) >= limit:
            return False
        _requests[key].append(now)
    return True
