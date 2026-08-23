"""
Rate Limiting Middleware and Dependency for ADEIP.

Provides sliding-window rate limiting keyed by Client IP or Authenticated User ID.
Injects standard rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After).
"""
import asyncio
import time
from typing import Callable, Dict, List, Optional
from fastapi import HTTPException, Request, Response, status

from app.core.config import settings


class InMemoryRateLimiter:
    """
    Sliding window in-memory rate limiter.
    """

    def __init__(self):
        # key -> list of timestamp floats
        self._records: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> Dict[str, int]:
        """
        Records the request and checks whether the limit was exceeded.
        Returns dict with limit, remaining, reset_after_seconds.
        Raises HTTPException(429) if exceeded.
        """
        if not settings.RATE_LIMIT_ENABLED:
            return {"limit": limit, "remaining": limit, "reset": 0}

        now = time.time()
        window_start = now - window_seconds

        async with self._lock:
            if key not in self._records:
                self._records[key] = []

            # Prune expired timestamps
            self._records[key] = [ts for ts in self._records[key] if ts > window_start]

            current_count = len(self._records[key])
            if current_count >= limit:
                oldest_ts = self._records[key][0]
                retry_after = max(1, int(oldest_ts + window_seconds - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {retry_after} second(s).",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(now + retry_after)),
                    },
                )

            # Record this hit
            self._records[key].append(now)
            remaining = max(0, limit - (current_count + 1))
            return {"limit": limit, "remaining": remaining, "reset": window_seconds}


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


def rate_limit(limit: int = 60, window_seconds: int = 60) -> Callable:
    """
    FastAPI dependency for applying rate limits to specific endpoints.
    Usage:
        @router.post("/login", dependencies=[Depends(rate_limit(limit=10, window_seconds=60))])
    """
    async def _rate_limit_dependency(request: Request, response: Response):
        client_ip = request.client.host if request.client else "unknown"
        # Combine endpoint path + IP for specific endpoint buckets
        key = f"{request.url.path}:{client_ip}"

        res = await rate_limiter.check_rate_limit(key=key, limit=limit, window_seconds=window_seconds)
        response.headers["X-RateLimit-Limit"] = str(res["limit"])
        response.headers["X-RateLimit-Remaining"] = str(res["remaining"])

    return _rate_limit_dependency
