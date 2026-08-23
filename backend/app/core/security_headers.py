"""
Security Headers Middleware for ADEIP.

Applies standard OWASP and NIST security headers to all HTTP responses:
- X-Content-Type-Options (nosniff)
- X-Frame-Options (DENY)
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
- Content-Security-Policy (CSP)
- Strict-Transport-Security (HSTS, when running over HTTPS)
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware injecting strict security headers into every outgoing HTTP response.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        if not settings.SECURITY_HEADERS_ENABLED:
            return response

        headers = response.headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "DENY"
        headers["X-XSS-Protection"] = "1; mode=block"
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(), payment=()"

        # Content-Security-Policy (CSP) allowing self resources and WebSocket connections
        headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline'; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none';"
        )

        # HSTS (Strict-Transport-Security) if request is HTTPS or in production
        if request.url.scheme == "https" or settings.APP_ENV == "production":
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        return response
