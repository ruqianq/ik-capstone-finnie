"""Tests for tool base functionality."""

import time
import pytest
from finnie.tools.base import CacheManager, RateLimiter, ToolWrapper


def test_cache_manager():
    """Test cache manager functionality."""
    cache = CacheManager(ttl=2)
    
    # Set and get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Get non-existent key
    assert cache.get("key2") is None
    
    # Test expiration
    cache.set("key3", "value3")
    time.sleep(2.5)
    assert cache.get("key3") is None
    
    # Clear cache
    cache.set("key4", "value4")
    cache.clear()
    assert cache.get("key4") is None


def test_rate_limiter():
    """Test rate limiter functionality."""
    limiter = RateLimiter(calls=2, period=1)
    
    # First call should be allowed
    assert limiter.allow() is True
    
    # Second call should be allowed
    assert limiter.allow() is True
    
    # Third call should be blocked
    assert limiter.allow() is False
    
    # Wait and try again
    time.sleep(1.5)
    assert limiter.allow() is True


def test_tool_wrapper():
    """Test tool wrapper base class."""
    tool = ToolWrapper("test_tool")
    
    assert tool.name == "test_tool"
    assert tool.call_count == 0
    assert tool.error_count == 0
    
    tool.record_call()
    assert tool.call_count == 1
    
    tool.record_error()
    assert tool.error_count == 1
    
    stats = tool.get_stats()
    assert stats["calls"] == 1
    assert stats["errors"] == 1


def test_cached_decorator():
    """Test cached decorator."""
    from finnie.tools.base import cached, cache_manager
    
    cache_manager.clear()
    call_count = [0]
    
    @cached(ttl=60)
    def expensive_function(x):
        call_count[0] += 1
        return x * 2
    
    # First call - should execute
    result1 = expensive_function(5)
    assert result1 == 10
    assert call_count[0] == 1
    
    # Second call - should use cache
    result2 = expensive_function(5)
    assert result2 == 10
    assert call_count[0] == 1  # Still 1, not called again


def test_rate_limited_decorator():
    """Test rate_limited decorator."""
    from finnie.tools.base import rate_limited, RateLimiter
    
    test_limiter = RateLimiter(calls=2, period=1)
    call_count = [0]
    
    @rate_limited
    def limited_function():
        call_count[0] += 1
        return call_count[0]
    
    # Calls should be limited
    result1 = limited_function()
    result2 = limited_function()
    
    assert result1 == 1
    assert result2 == 2
