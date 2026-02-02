"""ADK Router for intent classification and agent orchestration."""

from typing import Dict, List, Optional
from enum import Enum

from finnie.agents.base import BaseAgent, AgentType, AgentRequest, AgentResponse
from finnie.agents.finance_qa import FinanceQAAgent
from finnie.agents.portfolio import PortfolioAnalysisAgent
from finnie.agents.market import MarketAnalysisAgent
from finnie.agents.goals import GoalPlanningAgent
from finnie.observability import observability, log_with_trace, get_trace_id


class Intent(Enum):
    """User intent categories."""
    FINANCE_QA = "finance_qa"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    MARKET_ANALYSIS = "market_analysis"
    GOAL_PLANNING = "goal_planning"
    UNKNOWN = "unknown"


class ADKRouter:
    """Router for classifying intent and routing to appropriate agents."""
    
    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {
            AgentType.FINANCE_QA: FinanceQAAgent(),
            AgentType.PORTFOLIO_ANALYSIS: PortfolioAnalysisAgent(),
            AgentType.MARKET_ANALYSIS: MarketAnalysisAgent(),
            AgentType.GOAL_PLANNING: GoalPlanningAgent(),
        }
    
    def classify_intent(self, query: str, trace_id: str) -> Intent:
        """
        Classify user intent from query.
        
        Args:
            query: User's query
            trace_id: Trace ID for observability
            
        Returns:
            Classified intent
        """
        with observability.trace_operation(
            "router.classify_intent",
            attributes={"query": query, "trace_id": trace_id}
        ) as (span, _):
            query_lower = query.lower()
            
            # Portfolio analysis keywords
            if any(keyword in query_lower for keyword in [
                "portfolio", "holdings", "assets", "allocation",
                "diversification", "risk assessment"
            ]):
                intent = Intent.PORTFOLIO_ANALYSIS
            
            # Market analysis keywords
            elif any(keyword in query_lower for keyword in [
                "market", "stock price", "ticker", "trading",
                "trend", "technical", "chart", "nasdaq", "s&p"
            ]):
                intent = Intent.MARKET_ANALYSIS
            
            # Goal planning keywords
            elif any(keyword in query_lower for keyword in [
                "goal", "retirement", "save", "plan",
                "house", "home", "college", "education"
            ]):
                intent = Intent.GOAL_PLANNING
            
            # Finance Q&A (default for general questions)
            elif any(keyword in query_lower for keyword in [
                "what", "how", "why", "explain", "define",
                "bond", "etf", "mutual fund", "401k", "ira"
            ]):
                intent = Intent.FINANCE_QA
            
            else:
                intent = Intent.FINANCE_QA  # Default to Q&A
            
            span.set_attribute("intent", intent.value)
            log_with_trace(
                f"Classified intent: {intent.value}",
                trace_id=trace_id
            )
            
            return intent
    
    def route_to_agent(self, intent: Intent) -> Optional[BaseAgent]:
        """
        Route intent to appropriate agent.
        
        Args:
            intent: Classified intent
            
        Returns:
            Agent to handle the request, or None if unknown
        """
        intent_to_agent = {
            Intent.FINANCE_QA: AgentType.FINANCE_QA,
            Intent.PORTFOLIO_ANALYSIS: AgentType.PORTFOLIO_ANALYSIS,
            Intent.MARKET_ANALYSIS: AgentType.MARKET_ANALYSIS,
            Intent.GOAL_PLANNING: AgentType.GOAL_PLANNING,
        }
        
        agent_type = intent_to_agent.get(intent)
        return self.agents.get(agent_type) if agent_type else None
    
    async def process_request(
        self,
        query: str,
        context: Optional[Dict] = None,
        trace_id: Optional[str] = None
    ) -> AgentResponse:
        """
        Process a user request end-to-end.
        
        Args:
            query: User's query
            context: Additional context
            trace_id: Trace ID (generated if not provided)
            
        Returns:
            AgentResponse from the appropriate agent
        """
        # Generate trace ID if not provided
        if not trace_id:
            trace_id = get_trace_id()
        
        with observability.trace_operation(
            "router.process_request",
            attributes={"query": query, "trace_id": trace_id}
        ) as (span, _):
            log_with_trace(
                f"Processing request: {query}",
                trace_id=trace_id
            )
            
            # Classify intent
            intent = self.classify_intent(query, trace_id)
            span.set_attribute("intent", intent.value)
            
            # Route to agent
            agent = self.route_to_agent(intent)
            
            if not agent:
                log_with_trace(
                    f"No agent found for intent: {intent}",
                    trace_id=trace_id,
                    level="warning"
                )
                return AgentResponse(
                    response="I'm not sure how to help with that. Please try rephrasing your question.",
                    agent_type=AgentType.FINANCE_QA,
                    trace_id=trace_id,
                    metadata={"intent": intent.value},
                    confidence=0.0,
                )
            
            # Create agent request
            request = AgentRequest(
                query=query,
                context=context or {},
                trace_id=trace_id,
            )
            
            # Execute agent
            span.set_attribute("agent_type", agent.agent_type.value)
            response = await agent.execute(request)
            
            log_with_trace(
                f"Request completed by {agent.name} agent",
                trace_id=trace_id
            )
            
            return response
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent types."""
        return [agent_type.value for agent_type in self.agents.keys()]


# Global router instance
router = ADKRouter()
