"""
Security middleware following DevSecOps best practices
"""

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Callable, Dict
import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    Implements OWASP security header recommendations
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware
    For production, use Redis-based rate limiting
    """

    def __init__(self, app, rate_limit_per_minute: int = 60, burst: int = 100):
        super().__init__(app)
        self.rate_limit_per_minute = rate_limit_per_minute
        self.burst = burst
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 60  # Clean up old entries every minute
        self.last_cleanup = time.time()

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get client identifier for rate limiting
        Uses X-Forwarded-For if behind proxy, otherwise client IP
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup_old_requests(self):
        """Remove requests older than 1 minute"""
        if time.time() - self.last_cleanup < self.cleanup_interval:
            return

        cutoff = time.time() - 60
        for client in list(self.requests.keys()):
            self.requests[client] = [
                timestamp for timestamp in self.requests[client] if timestamp > cutoff
            ]
            if not self.requests[client]:
                del self.requests[client]

        self.last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health check
        if request.url.path == "/api/health":
            return await call_next(request)

        client_id = self._get_client_identifier(request)
        current_time = time.time()

        # Cleanup old requests periodically
        self._cleanup_old_requests()

        # Get requests in last minute
        recent_requests = [t for t in self.requests[client_id] if current_time - t < 60]

        # Check rate limit
        if len(recent_requests) >= self.burst:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {self.burst} requests per minute allowed",
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.burst),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + 60)),
                },
            )

        # Add current request
        self.requests[client_id].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, self.burst - len(recent_requests) - 1)
        response.headers["X-RateLimit-Limit"] = str(self.burst)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests for audit purposes
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Time: {process_time:.3f}s"
            )

            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"Error: {str(e)} "
                f"Time: {process_time:.3f}s"
            )
            raise
