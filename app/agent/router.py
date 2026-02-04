from opentelemetry import trace

from app.agent.finance_agent import FinanceAgent
from app.agent.portfolio_agent import PortfolioAgent
from app.agent.goal_agent import GoalPlanningAgent

tracer = trace.get_tracer(__name__)
finance_agent = FinanceAgent()
portfolio_agent = PortfolioAgent()
goal_agent = GoalPlanningAgent()

def route_and_process(user_input: str) -> str:
    """
    Routes user input to the appropriate agent.
    """
    # Intent Classification (Basic Heuristic)
    # If the query asks for "price", "stock", "market", or contains obvious tickers, try Portfolio Agent
    market_keywords = ["price", "stock", "market", "value", "quote", "add", "portfolio", "buy", "shares"]
    goal_keywords = ["goal", "save", "retire", "plan", "future"]
    
    query_lower = user_input.lower()
    
    if any(k in query_lower for k in goal_keywords):
        return goal_agent.process_query(user_input)
    
    is_market_query = any(k in query_lower for k in market_keywords) or user_input.isupper()
    
    if is_market_query:
        # Try Portfolio Agent
        response = portfolio_agent.process_query(user_input)
        # Fallback if Portfolio Agent didn't find tickers but it looked like a market query
        if "couldn't identify" in response:
             response = finance_agent.process_query(user_input)
    else:
        # Default to Finance Q&A
        response = finance_agent.process_query(user_input)

    return response
