"""
Rate limiting service for API endpoints
"""
import redis
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Request
from app.core.config import settings
from typing import Optional

# Redis client for rate limiting
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


class RateLimiter:
    """Rate limiting service using Redis"""
    
    @staticmethod
    def check_rate_limit(
        key: str, 
        limit: int, 
        window_seconds: int,
        identifier: Optional[str] = None
    ) -> bool:
        """
        Check if request is within rate limit
        
        Args:
            key: Base key for rate limiting (e.g., 'auth_login')
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
            identifier: Additional identifier (IP, user ID, etc.)
        
        Returns:
            True if within limit, raises HTTPException if exceeded
        """
        # Create unique key with identifier
        rate_key = f"rate_limit:{key}"
        if identifier:
            rate_key = f"{rate_key}:{identifier}"
        
        try:
            # Get current count
            current = redis_client.get(rate_key)
            
            if current is None:
                # First request in window
                redis_client.setex(rate_key, window_seconds, 1)
                return True
            
            current_count = int(current)
            
            if current_count >= limit:
                # Rate limit exceeded
                ttl = redis_client.ttl(rate_key)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {ttl} seconds.",
                    headers={"Retry-After": str(ttl)}
                )
            
            # Increment counter
            redis_client.incr(rate_key)
            return True
            
        except redis.RedisError:
            # If Redis is down, allow the request (fail open)
            return True
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


def rate_limit_auth(request: Request) -> bool:
    """Rate limiter for authentication endpoints"""
    client_ip = RateLimiter.get_client_ip(request)
    
    # 5 attempts per minute per IP for auth endpoints
    return RateLimiter.check_rate_limit(
        key="auth",
        limit=5,
        window_seconds=60,
        identifier=client_ip
    )


def rate_limit_password_reset(request: Request) -> bool:
    """Rate limiter for password reset endpoints"""
    client_ip = RateLimiter.get_client_ip(request)
    
    # 3 attempts per hour per IP for password reset
    return RateLimiter.check_rate_limit(
        key="password_reset",
        limit=3,
        window_seconds=3600,
        identifier=client_ip
    )


def rate_limit_user_auth(request: Request, user_id: str) -> bool:
    """Rate limiter per user for authentication actions"""
    # 10 attempts per hour per user
    return RateLimiter.check_rate_limit(
        key="user_auth",
        limit=10,
        window_seconds=3600,
        identifier=user_id
    )


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass


class AsyncRateLimiter:
    """Async rate limiter for content generation endpoints"""
    
    def __init__(self):
        self.limiter = RateLimiter()
    
    async def check_rate_limit(self, key: str, limit: int = 60, window_seconds: int = 60):
        """Check rate limit asynchronously"""
        try:
            self.limiter.check_rate_limit(key, limit, window_seconds)
        except HTTPException as e:
            if e.status_code == 429:
                raise RateLimitExceeded(e.detail)
            raise


# Global rate limiter instance
rate_limiter = AsyncRateLimiter()