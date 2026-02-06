"""
Router module for FinnIE multi-agent system.

Supports two routing modes:
1. LangGraph (default): LLM-based intent classification with StateGraph orchestration
2. Keyword-based (fallback): Fast heuristic routing based on keyword matching

Set USE_LANGGRAPH=false in environment to use keyword-based routing.
"""

import os
from opentelemetry import trace

from app.agent.finance_agent import FinanceAgent
from app.agent.portfolio_agent import PortfolioAgent
from app.agent.goal_agent import GoalPlanningAgent
from app.agent.market_agent import MarketAnalysisAgent
from app.agent.news_agent import NewsSynthesizerAgent
from app.agent.tax_agent import TaxEducationAgent

tracer = trace.get_tracer(__name__)

# Configuration
USE_LANGGRAPH = os.getenv("USE_LANGGRAPH", "true").lower() == "true"
USE_ORCHESTRATOR = os.getenv("USE_ORCHESTRATOR", "false").lower() == "true"

# Initialize agents (used by both routing modes)
finance_agent = FinanceAgent()
portfolio_agent = PortfolioAgent()
goal_agent = GoalPlanningAgent()
market_agent = MarketAnalysisAgent()
news_agent = NewsSynthesizerAgent()
tax_agent = TaxEducationAgent()

# Lazy-load LangGraph workflow
_langgraph_workflow = None


def _get_langgraph_workflow():
    """Lazy initialization of LangGraph workflow."""
    global _langgraph_workflow
    if _langgraph_workflow is None:
        from app.workflow.graph import FinancialWorkflow
        _langgraph_workflow = FinancialWorkflow()
    return _langgraph_workflow


# Lazy-load Orchestrator workflow
_orchestrator_workflow = None


def _get_orchestrator_workflow():
    """Lazy initialization of orchestrator workflow."""
    global _orchestrator_workflow
    if _orchestrator_workflow is None:
        from app.workflow.orchestrator import OrchestratorWorkflow
        _orchestrator_workflow = OrchestratorWorkflow()
    return _orchestrator_workflow


def route_and_process(user_input: str, context: str = None) -> str:
    """
    Routes user input to the appropriate agent(s).

    Supports three routing modes with cascading fallback:
    1. Orchestrator (USE_ORCHESTRATOR=true): Multi-agent supervisor pattern
    2. LangGraph (USE_LANGGRAPH=true): Single-agent LLM-based routing
    3. Keyword-based: Fast heuristic routing (always available as fallback)

    Args:
        user_input: The user's query
        context: Optional context from previous conversation turns

    Returns:
        Response string from the appropriate agent(s)
    """
    with tracer.start_as_current_span("route_and_process") as span:
        span.set_attribute("input.value", user_input)

        # Determine routing mode
        if USE_ORCHESTRATOR:
            mode = "orchestrator"
        elif USE_LANGGRAPH:
            mode = "langgraph"
        else:
            mode = "keyword"
        span.set_attribute("routing.mode", mode)

        # 1. Try orchestrator (multi-agent supervisor)
        if USE_ORCHESTRATOR:
            try:
                orchestrator = _get_orchestrator_workflow()
                result = orchestrator.invoke(user_input, context=context)
                response = result.get("response", "")
                agents_used = result.get("agents_used", [])

                span.set_attribute("routing.agents_used", str(agents_used))
                span.set_attribute("routing.plan", str(result.get("plan", [])))
                span.set_attribute("routing.reasoning", result.get("reasoning", ""))

                if response:
                    return response
            except Exception as e:
                span.set_attribute("routing.orchestrator_error", str(e))
                print(f"Orchestrator failed, falling back: {e}")

        # 2. Try LangGraph single-dispatch
        if USE_LANGGRAPH:
            try:
                workflow = _get_langgraph_workflow()
                result = workflow.invoke(user_input, context=context)
                response = result.get("response", "")
                intent = result.get("intent", "unknown")

                span.set_attribute("routing.intent", intent)

                if response:
                    return response
            except Exception as e:
                span.set_attribute("routing.langgraph_error", str(e))
                print(f"LangGraph routing failed, falling back to keywords: {e}")

        # 3. Keyword-based routing (final fallback)
        return _keyword_based_routing(user_input)


def _keyword_based_routing(user_input: str) -> str:
    """
    Keyword-based routing fallback.

    Fast heuristic routing based on keyword matching.
    """
    query_lower = user_input.lower()

    # Tax-related keywords
    tax_keywords = [
        "tax", "401k", "401(k)", "ira", "roth", "hsa", "529",
        "capital gain", "deduction", "contribution limit", "tax-loss",
        "harvesting", "wash sale"
    ]

    # News-related keywords
    news_keywords = [
        "news", "headline", "latest", "today's", "recent",
        "what's happening", "market update"
    ]

    # Market analysis keywords
    market_analysis_keywords = [
        "market overview", "market summary", "sector", "trend",
        "technical analysis", "moving average", "rsi", "vix",
        "s&p 500", "s&p", "dow jones", "nasdaq", "how is the market", "market today"
    ]

    # Goal planning keywords
    goal_keywords = [
        "goal", "save for", "saving for", "want to save", "need to save",
        "retire", "retirement", "plan for", "financial plan",
        "how much to save", "down payment", "emergency fund",
        "years from now", "in 3 years", "in 5 years", "in 10 years"
    ]

    # Portfolio/trading keywords
    portfolio_keywords = [
        "price", "stock price", "quote", "add", "portfolio",
        "buy", "shares", "my holdings", "how much is"
    ]

    # Route based on intent priority

    # 1. Tax queries
    if any(k in query_lower for k in tax_keywords):
        return tax_agent.process_query(user_input)

    # 2. News queries
    if any(k in query_lower for k in news_keywords):
        return news_agent.process_query(user_input)

    # 3. Market analysis queries
    if any(k in query_lower for k in market_analysis_keywords):
        return market_agent.process_query(user_input)

    # 4. Goal planning queries
    if any(k in query_lower for k in goal_keywords):
        return goal_agent.process_query(user_input)

    # 5. Portfolio/specific stock queries
    if any(k in query_lower for k in portfolio_keywords) or user_input.isupper():
        response = portfolio_agent.process_query(user_input)
        if "couldn't identify" in response:
            response = finance_agent.process_query(user_input)
        return response

    # 6. Default to Finance Q&A
    return finance_agent.process_query(user_input)
