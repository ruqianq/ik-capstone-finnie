"""Tests for base agent functionality."""
import pytest
from finnie.agents.base_agent import FinancialAgent


def test_agent_initialization(sample_agent_config, mock_api_key):
    """Test FinancialAgent initialization."""
    agent = FinancialAgent("test_agent", sample_agent_config, mock_api_key)
    
    assert agent.name == "test_agent"
    assert agent.model_name == "gemini-1.5-flash"
    assert agent.system_prompt == "You are a test financial advisor."


def test_agent_get_info(sample_agent_config, mock_api_key):
    """Test getting agent information."""
    agent = FinancialAgent("test_agent", sample_agent_config, mock_api_key)
    info = agent.get_info()
    
    assert info["name"] == "test_agent"
    assert info["description"] == "A test financial agent"
    assert info["model"] == "gemini-1.5-flash"
