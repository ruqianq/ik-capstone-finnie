"""Test configuration for pytest."""
import pytest
import os


@pytest.fixture
def mock_api_key():
    """Mock Google API key for testing."""
    return "test_api_key_12345"


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for testing."""
    return {
        "name": "Test Agent",
        "description": "A test financial agent",
        "model": "gemini-1.5-flash",
        "system_prompt": "You are a test financial advisor."
    }


@pytest.fixture
def sample_query():
    """Sample user query for testing."""
    return "How should I manage my budget?"
