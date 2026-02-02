"""Tests for observability integration."""
import pytest
from finnie.utils.observability import PhoenixObservability


def test_observability_initialization():
    """Test PhoenixObservability initialization."""
    obs = PhoenixObservability(endpoint="http://localhost:6006")
    assert obs.endpoint == "http://localhost:6006"
    assert obs.enable_tracing is True
    assert obs.is_initialized() is False


def test_observability_disabled():
    """Test PhoenixObservability with tracing disabled."""
    obs = PhoenixObservability(enable_tracing=False)
    obs.setup()
    # Should not initialize when tracing is disabled
    assert obs.is_initialized() is False


def test_observability_default_endpoint():
    """Test default endpoint configuration."""
    obs = PhoenixObservability()
    assert "6006" in obs.endpoint or "localhost" in obs.endpoint
