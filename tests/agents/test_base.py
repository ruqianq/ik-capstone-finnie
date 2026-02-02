"""Tests for base agent functionality."""

import pytest
from finnie.agents.base import BaseAgent, AgentType, AgentRequest, AgentResponse


class TestAgent(BaseAgent):
    """Test agent implementation."""
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(
            response="Test response",
            agent_type=self.agent_type,
            trace_id=request.trace_id,
            metadata={"test": "data"},
        )


@pytest.mark.asyncio
async def test_base_agent_execution():
    """Test base agent execution with tracing."""
    agent = TestAgent(AgentType.FINANCE_QA)
    
    request = AgentRequest(
        query="test query",
        context={},
        trace_id="test-trace-123"
    )
    
    response = await agent.execute(request)
    
    assert response.response == "Test response"
    assert response.agent_type == AgentType.FINANCE_QA
    assert response.trace_id == "test-trace-123"
    assert response.metadata["test"] == "data"


def test_agent_validate_request():
    """Test request validation."""
    agent = TestAgent(AgentType.FINANCE_QA)
    
    # Valid request
    valid_request = AgentRequest(
        query="test query",
        context={},
        trace_id="test-trace-123"
    )
    assert agent.validate_request(valid_request) is True
    
    # Invalid request (no query)
    invalid_request = AgentRequest(
        query="",
        context={},
        trace_id="test-trace-123"
    )
    assert agent.validate_request(invalid_request) is False


def test_agent_type_enum():
    """Test AgentType enum."""
    assert AgentType.FINANCE_QA.value == "finance_qa"
    assert AgentType.PORTFOLIO_ANALYSIS.value == "portfolio_analysis"
    assert AgentType.MARKET_ANALYSIS.value == "market_analysis"
    assert AgentType.GOAL_PLANNING.value == "goal_planning"
