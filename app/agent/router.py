from opentelemetry import trace

from app.agent.finance_agent import FinanceAgent
from app.agent.portfolio_agent import PortfolioAgent
from app.agent.goal_agent import GoalPlanningAgent
from app.agent.market_agent import MarketAnalysisAgent
from app.agent.news_agent import NewsSynthesizerAgent
from app.agent.tax_agent import TaxEducationAgent

tracer = trace.get_tracer(__name__)

# Initialize all agents
finance_agent = FinanceAgent()
portfolio_agent = PortfolioAgent()
goal_agent = GoalPlanningAgent()
market_agent = MarketAnalysisAgent()
news_agent = NewsSynthesizerAgent()
tax_agent = TaxEducationAgent()


def route_and_process(user_input: str) -> str:
    """
    Routes user input to the appropriate agent based on intent classification.

    Agent routing priority:
    1. Tax Education Agent - tax-related queries
    2. News Synthesizer Agent - news-related queries
    3. Market Analysis Agent - market overview, trends, technical analysis
    4. Goal Planning Agent - financial goals and planning
    5. Portfolio Agent - portfolio management, stock prices, trades
    6. Finance Q&A Agent - general financial education (default)
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

    # Market analysis keywords (broader market, not specific stocks)
    # Note: "dow" changed to "dow jones" to avoid matching "down" (payment)
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

    # 3. Market analysis queries (trends, sectors, technical)
    if any(k in query_lower for k in market_analysis_keywords):
        return market_agent.process_query(user_input)

    # 4. Goal planning queries
    if any(k in query_lower for k in goal_keywords):
        return goal_agent.process_query(user_input)

    # 5. Portfolio/specific stock queries
    if any(k in query_lower for k in portfolio_keywords) or user_input.isupper():
        response = portfolio_agent.process_query(user_input)
        # Fallback to finance agent if portfolio agent couldn't help
        if "couldn't identify" in response:
            response = finance_agent.process_query(user_input)
        return response

    # 6. Default to Finance Q&A for general education
    return finance_agent.process_query(user_input)
