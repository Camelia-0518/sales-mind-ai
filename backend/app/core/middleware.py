"""
Rate limiting and security middleware
"""
from fastapi import Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Dict, Tuple
import redis

from app.core.config import settings

# Simple in-memory rate limiting (use Redis in production)
class RateLimiter:
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.local_cache: Dict[str, Tuple[int, float]] = {}

    def is_allowed(self, key: str, max_requests: int, window: int) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()

        if self.redis:
            # Redis-based rate limiting
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            results = pipe.execute()
            count = results[0]
            return count <= max_requests
        else:
            # Memory-based rate limiting
            count, start = self.local_cache.get(key, (0, now))

            if now - start > window:
                # Reset window
                self.local_cache[key] = (1, now)
                return True

            if count >= max_requests:
                return False

            self.local_cache[key] = (count + 1, start)
            return True


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.headers.get("X-Forwarded-For", request.client.host)

        # Different limits for different endpoints
        path = request.url.path

        if "/auth/" in path:
            # Stricter limits for auth endpoints
            key = f"auth:{client_ip}"
            max_requests = 5
            window = 60  # 5 requests per minute
        elif "/api/" in path:
            # General API limits
            key = f"api:{client_ip}"
            max_requests = 100
            window = 60  # 100 requests per minute
        else:
            return await call_next(request)

        if not rate_limiter.is_allowed(key, max_requests, window):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(window)}
            )

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log request (in production, use proper logging)
        print(f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")

        # Add response time header
        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        return response


def setup_middleware(app):
    """Setup all middleware for the application"""

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://salesmind.ai"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting
    app.add_middleware(RateLimitMiddleware)

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)
