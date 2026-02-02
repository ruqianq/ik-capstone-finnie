"""Tests for router functionality."""

import pytest
from finnie.agents.router import ADKRouter, Intent
from finnie.agents.base import AgentType


def test_router_initialization():
    """Test router initialization."""
    router = ADKRouter()
    
    assert len(router.agents) == 4
    assert AgentType.FINANCE_QA in router.agents
    assert AgentType.PORTFOLIO_ANALYSIS in router.agents
    assert AgentType.MARKET_ANALYSIS in router.agents
    assert AgentType.GOAL_PLANNING in router.agents


def test_intent_classification():
    """Test intent classification."""
    router = ADKRouter()
    
    # Finance Q&A
    assert router.classify_intent("What is a stock?", "test-trace") == Intent.FINANCE_QA
    assert router.classify_intent("Explain bonds", "test-trace") == Intent.FINANCE_QA
    
    # Portfolio Analysis
    assert router.classify_intent("Analyze my portfolio", "test-trace") == Intent.PORTFOLIO_ANALYSIS
    assert router.classify_intent("What's my asset allocation?", "test-trace") == Intent.PORTFOLIO_ANALYSIS
    
    # Market Analysis
    assert router.classify_intent("What's the stock price of AAPL?", "test-trace") == Intent.MARKET_ANALYSIS
    assert router.classify_intent("Show me market trends", "test-trace") == Intent.MARKET_ANALYSIS
    
    # Goal Planning
    assert router.classify_intent("Help me plan for retirement", "test-trace") == Intent.GOAL_PLANNING
    assert router.classify_intent("I want to save for a house", "test-trace") == Intent.GOAL_PLANNING


def test_route_to_agent():
    """Test routing to agents."""
    router = ADKRouter()
    
    agent = router.route_to_agent(Intent.FINANCE_QA)
    assert agent is not None
    assert agent.agent_type == AgentType.FINANCE_QA
    
    agent = router.route_to_agent(Intent.PORTFOLIO_ANALYSIS)
    assert agent is not None
    assert agent.agent_type == AgentType.PORTFOLIO_ANALYSIS
    
    agent = router.route_to_agent(Intent.UNKNOWN)
    assert agent is None


@pytest.mark.asyncio
async def test_process_request():
    """Test end-to-end request processing."""
    router = ADKRouter()
    
    response = await router.process_request(
        query="What is a stock?",
        context={},
        trace_id="test-trace-123"
    )
    
    assert response is not None
    assert response.trace_id == "test-trace-123"
    assert response.agent_type == AgentType.FINANCE_QA
    assert len(response.response) > 0


def test_get_available_agents():
    """Test getting available agents."""
    router = ADKRouter()
    
    agents = router.get_available_agents()
    assert len(agents) == 4
    assert "finance_qa" in agents
    assert "portfolio_analysis" in agents
    assert "market_analysis" in agents
    assert "goal_planning" in agents
