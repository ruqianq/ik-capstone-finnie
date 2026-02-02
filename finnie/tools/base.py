"""Tool wrappers with caching, retry, and rate limiting."""

import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
from collections import defaultdict
import threading

from tenacity import retry, stop_after_attempt, wait_exponential

from finnie.config import config
from finnie.observability import log_with_trace


class CacheManager:
    """Simple TTL-based cache manager."""
    
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self.cache: Dict[str, tuple] = {}  # key -> (value, timestamp)
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    return value
                else:
                    del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache with current timestamp."""
        with self.lock:
            self.cache[key] = (value, time.time())
    
    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, calls: int = 60, period: int = 60):
        self.calls = calls
        self.period = period
        self.allowance = calls
        self.last_check = time.time()
        self.lock = threading.Lock()
    
    def allow(self) -> bool:
        """Check if request is allowed under rate limit."""
        with self.lock:
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current
            
            self.allowance += time_passed * (self.calls / self.period)
            if self.allowance > self.calls:
                self.allowance = self.calls
            
            if self.allowance < 1.0:
                return False
            else:
                self.allowance -= 1.0
                return True
    
    def wait(self):
        """Wait until request is allowed."""
        while not self.allow():
            time.sleep(0.1)


# Global instances
cache_manager = CacheManager(ttl=config.cache.ttl)
rate_limiter = RateLimiter(
    calls=config.cache.rate_limit_calls,
    period=config.cache.rate_limit_period
)


def cached(ttl: Optional[int] = None):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds (uses default if None)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                log_with_trace(f"Cache hit for {func.__name__}", level="debug")
                return cached_result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result)
            log_with_trace(f"Cache miss for {func.__name__}", level="debug")
            
            return result
        return wrapper
    return decorator


def rate_limited(func: Callable):
    """
    Decorator for rate limiting function calls.
    
    Args:
        func: Function to rate limit
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        rate_limiter.wait()
        return func(*args, **kwargs)
    return wrapper


def with_retry(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10
):
    """
    Decorator for retrying function calls with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries
        max_wait: Maximum wait time between retries
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        reraise=True,
    )


class ToolWrapper:
    """Base class for tool wrappers."""
    
    def __init__(self, name: str):
        self.name = name
        self.call_count = 0
        self.error_count = 0
    
    def record_call(self):
        """Record a successful call."""
        self.call_count += 1
    
    def record_error(self):
        """Record an error."""
        self.error_count += 1
    
    def get_stats(self) -> Dict[str, int]:
        """Get tool usage statistics."""
        return {
            "calls": self.call_count,
            "errors": self.error_count,
        }
