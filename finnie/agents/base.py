"""Base agent interface for FinnIE multi-agent system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from finnie.observability import observability, log_with_trace


class AgentType(Enum):
    """Types of agents in the system."""
    FINANCE_QA = "finance_qa"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    MARKET_ANALYSIS = "market_analysis"
    GOAL_PLANNING = "goal_planning"


@dataclass
class AgentRequest:
    """Request data for an agent."""
    query: str
    context: Dict[str, Any]
    trace_id: str
    user_id: Optional[str] = None


@dataclass
class AgentResponse:
    """Response from an agent."""
    response: str
    agent_type: AgentType
    trace_id: str
    metadata: Dict[str, Any]
    citations: Optional[List[str]] = None
    confidence: float = 1.0


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.name = agent_type.value
    
    @abstractmethod
    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process a request and return a response.
        
        Args:
            request: The agent request containing query and context
            
        Returns:
            AgentResponse with the result
        """
        pass
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute the agent with tracing.
        
        Args:
            request: The agent request
            
        Returns:
            AgentResponse with the result
        """
        with observability.trace_operation(
            f"agent.{self.name}",
            attributes={
                "agent.type": self.name,
                "query": request.query,
                "trace_id": request.trace_id,
            }
        ) as (span, _):
            log_with_trace(
                f"Executing {self.name} agent",
                trace_id=request.trace_id
            )
            
            try:
                response = await self.process(request)
                span.set_attribute("success", True)
                span.set_attribute("confidence", response.confidence)
                
                log_with_trace(
                    f"{self.name} agent completed successfully",
                    trace_id=request.trace_id
                )
                
                return response
                
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                log_with_trace(
                    f"Error in {self.name} agent: {e}",
                    trace_id=request.trace_id,
                    level="error"
                )
                raise
    
    def validate_request(self, request: AgentRequest) -> bool:
        """
        Validate the request before processing.
        
        Args:
            request: The agent request to validate
            
        Returns:
            True if valid, False otherwise
        """
        return bool(request.query and request.trace_id)
