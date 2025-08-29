"""
Security middleware for enhanced application protection
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import traceback
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
import re

logger = logging.getLogger(__name__)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    def __init__(self, app, enable_csp: bool = True, enable_hsts: bool = True):
        super().__init__(app)
        self.enable_csp = enable_csp
        self.enable_hsts = enable_hsts
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Content Security Policy
        if self.enable_csp:
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net",
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net",
                "img-src 'self' data: blob:",
                "font-src 'self' cdn.jsdelivr.net",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'"
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # HTTP Strict Transport Security (HSTS)
        if self.enable_hsts and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        permissions_policy = [
            "geolocation=()",
            "camera=()",
            "microphone=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_policy)
        
        # Remove server information
        response.headers.pop("Server", None)
        
        return response

class ErrorSanitizationMiddleware(BaseHTTPMiddleware):
    """Sanitize error messages to prevent information leakage"""
    
    def __init__(self, app, debug_mode: bool = False):
        super().__init__(app)
        self.debug_mode = debug_mode
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            
            if self.debug_mode:
                # In debug mode, return detailed error information
                error_detail = {
                    "error": str(exc),
                    "type": type(exc).__name__,
                    "traceback": traceback.format_exc()
                }
            else:
                # In production, return sanitized error
                if isinstance(exc, HTTPException):
                    # For HTTP exceptions, use the detail if it's safe
                    safe_detail = self._sanitize_error_message(exc.detail)
                    error_detail = {"error": safe_detail}
                    status_code = exc.status_code
                else:
                    # For other exceptions, return generic message
                    error_detail = {"error": "An internal server error occurred"}
                    status_code = 500
                
                return JSONResponse(
                    status_code=status_code,
                    content=error_detail
                )
    
    def _sanitize_error_message(self, message: str) -> str:
        """Sanitize error messages to remove sensitive information"""
        if not isinstance(message, str):
            return "Invalid request"
        
        # Remove file paths
        message = re.sub(r'/[a-zA-Z0-9_/\-\.]+\.py', '[FILE_PATH]', message)
        
        # Remove SQL details
        message = re.sub(r'(DETAIL|HINT|CONTEXT):.*', '', message)
        
        # Remove database connection strings
        message = re.sub(r'postgresql://[^/\s]+', '[DATABASE_URL]', message)
        
        # Remove stack trace patterns
        message = re.sub(r'File "[^"]+", line \d+', '[FILE_REFERENCE]', message)
        
        # Remove specific error codes that might leak info
        message = re.sub(r'Error \d{4,}:', 'Error:', message)
        
        # Limit message length
        if len(message) > 200:
            message = message[:200] + "..."
        
        return message

def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom rate limit handler
    """
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"message": f"Rate limit exceeded: {exc.detail}"}
    )
    response = request.app.state.limiter._inject_headers(response, request.state.view_rate_limit)
    return response

def setup_rate_limiting(app):
    """Setup rate limiting for the application"""
    from slowapi.middleware import SlowAPIMiddleware
    
    # Add rate limiting middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    return limiter

# Rate limiting decorators for different endpoint types
def auth_rate_limit():
    """Rate limit for authentication endpoints (stricter)"""
    return limiter.limit("5/minute")

def api_rate_limit():
    """Rate limit for general API endpoints"""
    return limiter.limit("60/minute")

def file_upload_rate_limit():
    """Rate limit for file upload endpoints"""
    return limiter.limit("10/minute")

def admin_rate_limit():
    """Rate limit for admin endpoints"""
    return limiter.limit("30/minute")
