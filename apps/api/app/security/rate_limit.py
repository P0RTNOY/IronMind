import time
import threading
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException, status, Depends

from app.config import settings
from app.models import UserContext

class RateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._windows: Dict[str, List[float]] = {}

    def is_allowed(self, key: str, max_requests: int, window_seconds: int, now: float = None) -> Tuple[bool, int, int]:
        if now is None:
            now = time.monotonic()
            
        cutoff = now - window_seconds
        
        with self._lock:
            records = self._windows.get(key, [])
            valid_records = [t for t in records if t > cutoff]
            
            allowed = len(valid_records) < max_requests
            if allowed:
                valid_records.append(now)
                
            self._windows[key] = valid_records
            
            remaining = max(0, max_requests - len(valid_records))
            if valid_records:
                reset_in = int((valid_records[0] + window_seconds) - now)
            else:
                reset_in = window_seconds
                
            return allowed, remaining, max(0, reset_in)
            
    def clear(self):
        """For testing"""
        with self._lock:
            self._windows.clear()

limiter = RateLimiter()

def get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def create_rate_limiter_ip(route_name: str, max_requests: int, window_seconds: int):
    def dependency(request: Request):
        ip = get_client_ip(request)
        key = f"rl:ip:{route_name}:{ip}"
        
        allowed, remaining, reset_in = limiter.is_allowed(key, max_requests, window_seconds)
        if not allowed:
            reset_epoch = int(time.time() + reset_in)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate_limited",
                headers={
                    "Retry-After": str(reset_in),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_epoch)
                }
            )
    return dependency

def create_rate_limiter_uid(route_name: str, max_requests: int, window_seconds: int):
    # Lazy import to avoid circular dependencies
    from app.deps import get_current_user
    
    def dependency(user: UserContext = Depends(get_current_user)) -> UserContext:
        key = f"rl:uid:{route_name}:{user.uid}"
        allowed, remaining, reset_in = limiter.is_allowed(key, max_requests, window_seconds)
        if not allowed:
            reset_epoch = int(time.time() + reset_in)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate_limited",
                headers={
                    "Retry-After": str(reset_in),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_epoch)
                }
            )
        return user
    return dependency

def create_rate_limiter_webhook(route_name: str, max_requests: int, window_seconds: int):
    def dependency(request: Request):
        if not settings.WEBHOOK_RATE_LIMIT_ENABLED:
            return
            
        ip = get_client_ip(request)
        key = f"rl:webhook:{route_name}:{ip}"
        allowed, remaining, reset_in = limiter.is_allowed(key, max_requests, window_seconds)
        if not allowed:
            reset_epoch = int(time.time() + reset_in)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate_limited",
                headers={
                    "Retry-After": str(reset_in),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_epoch)
                }
            )
    return dependency
