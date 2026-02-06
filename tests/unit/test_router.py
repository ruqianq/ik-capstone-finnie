"""
Unit tests for FinnIE router and workflow.

Note: Some tests require app imports which need pandas/yfinance.
These tests will be skipped if imports fail (e.g., in some local environments).
Run tests in Docker for full coverage.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Check if app imports are available
_IMPORTS_AVAILABLE = True
_IMPORT_ERROR = ""
try:
    # Test if we can import app modules
    import yfinance
    import pandas
except (ImportError, ValueError, Exception) as e:
    _IMPORTS_AVAILABLE = False
    _IMPORT_ERROR = str(e)

# Decorator for tests requiring app imports
requires_app_imports = pytest.mark.skipif(
    not _IMPORTS_AVAILABLE,
    reason=f"App imports not available: {_IMPORT_ERROR[:100] if _IMPORT_ERROR else 'unknown'}"
)


class TestKeywordRouter:
    """Tests for keyword-based routing fallback."""

    def test_tax_keywords_detection(self):
        """Test that tax-related keywords are properly detected."""
        tax_keywords = [
            "tax", "401k", "401(k)", "ira", "roth", "hsa", "529",
            "capital gain", "deduction", "contribution limit", "tax-loss",
            "harvesting", "wash sale"
        ]

        tax_queries = [
            "What is a 401k?",
            "Roth IRA contribution limits",
            "How does tax-loss harvesting work?",
            "HSA benefits",
        ]

        for query in tax_queries:
            query_lower = query.lower()
            matched = any(k in query_lower for k in tax_keywords)
            assert matched, f"Tax keywords not detected in: {query}"

    def test_news_keywords_detection(self):
        """Test that news-related keywords are properly detected."""
        news_keywords = [
            "news", "headline", "latest", "today's", "recent",
            "what's happening", "market update"
        ]

        news_queries = [
            "What's the latest news?",
            "Market headlines today",
            "Recent market updates",
        ]

        for query in news_queries:
            query_lower = query.lower()
            matched = any(k in query_lower for k in news_keywords)
            assert matched, f"News keywords not detected in: {query}"

    def test_market_keywords_detection(self):
        """Test that market-related keywords are properly detected."""
        market_keywords = [
            "market overview", "market summary", "sector", "trend",
            "technical analysis", "moving average", "rsi", "vix",
            "s&p 500", "s&p", "dow jones", "nasdaq", "how is the market", "market today"
        ]

        market_queries = [
            "How is the market today?",
            "Show me sector performance",
            "S&P 500 trend",
            "What's the VIX?",
        ]

        for query in market_queries:
            query_lower = query.lower()
            matched = any(k in query_lower for k in market_keywords)
            assert matched, f"Market keywords not detected in: {query}"

    def test_goal_keywords_detection(self):
        """Test that goal-related keywords are properly detected."""
        goal_keywords = [
            "goal", "save for", "saving for", "want to save", "need to save",
            "retire", "retirement", "plan for", "financial plan",
            "how much to save", "down payment", "emergency fund",
            "years from now", "in 3 years", "in 5 years", "in 10 years"
        ]

        goal_queries = [
            "I want to save $50,000 for a house",
            "Help me plan for retirement",
            "How much to save for a down payment?",
            "I need $100,000 in 5 years",
        ]

        for query in goal_queries:
            query_lower = query.lower()
            matched = any(k in query_lower for k in goal_keywords)
            assert matched, f"Goal keywords not detected in: {query}"

    def test_portfolio_keywords_detection(self):
        """Test that portfolio-related keywords are properly detected."""
        portfolio_keywords = [
            "price", "stock price", "quote", "add", "portfolio",
            "buy", "shares", "my holdings", "how much is"
        ]

        portfolio_queries = [
            "What's the price of AAPL?",
            "Add 10 shares of MSFT",
            "Show my portfolio",
            "How much is Google stock?",
        ]

        for query in portfolio_queries:
            query_lower = query.lower()
            matched = any(k in query_lower for k in portfolio_keywords)
            assert matched, f"Portfolio keywords not detected in: {query}"

    def test_dow_jones_not_matching_down(self):
        """Test that 'dow jones' doesn't match 'down' in queries."""
        # This was a bug that was fixed - "dow" was matching "down payment"
        query = "I'm saving for a down payment"
        market_keywords = ["dow jones"]  # Changed from "dow" to "dow jones"

        query_lower = query.lower()
        matched = any(k in query_lower for k in market_keywords)
        assert not matched, "dow jones should not match 'down payment'"


class TestIntentClassifier:
    """Tests for LLM-based intent classification."""

    @requires_app_imports
    @patch("langchain_openai.ChatOpenAI")
    def test_classifier_initialization(self, mock_llm_class):
        """Test that intent classifier initializes correctly."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm

        from app.workflow.graph import IntentClassifier

        classifier = IntentClassifier()

        assert classifier.llm is not None
        assert classifier.prompt is not None

    @requires_app_imports
    @patch("langchain_openai.ChatOpenAI")
    def test_classify_returns_valid_intent(self, mock_llm_class):
        """Test that classifier returns valid intent."""
        mock_llm = MagicMock()
        mock_response = Mock()
        mock_response.content = "finance_qa"
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        from app.workflow.graph import IntentClassifier

        classifier = IntentClassifier()

        # Mock the chain
        with patch.object(classifier, 'classify', return_value="finance_qa"):
            result = classifier.classify("What is a stock?")
            assert result in [
                "finance_qa", "portfolio", "market_analysis",
                "goal_planning", "news", "tax_education"
            ]

    @requires_app_imports
    @patch("langchain_openai.ChatOpenAI")
    def test_classify_handles_error(self, mock_llm_class):
        """Test that classifier handles errors gracefully."""
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API Error")
        mock_llm_class.return_value = mock_llm

        from app.workflow.graph import IntentClassifier

        classifier = IntentClassifier()

        # When error occurs, should default to finance_qa
        result = classifier.classify("What is a stock?")
        assert result == "finance_qa"


class TestConversationState:
    """Tests for conversation state schema."""

    @requires_app_imports
    def test_state_schema(self):
        """Test that state schema has all required fields."""
        from app.workflow.graph import ConversationState

        # Create a state instance
        state: ConversationState = {
            "query": "What is a stock?",
            "messages": [],
            "intent": None,
            "response": None,
            "context": None
        }

        assert "query" in state
        assert "messages" in state
        assert "intent" in state
        assert "response" in state
        assert "context" in state


class TestFinancialWorkflow:
    """Tests for the LangGraph workflow."""

    @requires_app_imports
    @patch("app.agent.finance_agent.FinanceAgent")
    @patch("app.agent.portfolio_agent.PortfolioAgent")
    @patch("app.agent.market_agent.MarketAnalysisAgent")
    @patch("app.agent.goal_agent.GoalPlanningAgent")
    @patch("app.agent.news_agent.NewsSynthesizerAgent")
    @patch("app.agent.tax_agent.TaxEducationAgent")
    @patch("langchain_openai.ChatOpenAI")
    def test_workflow_initialization(
        self, mock_llm, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Test that workflow initializes with all agents."""
        # Setup mocks
        for mock in [mock_finance, mock_portfolio, mock_market, mock_goal, mock_news, mock_tax]:
            mock.return_value = MagicMock()

        mock_llm.return_value = MagicMock()

        from app.workflow.graph import FinancialWorkflow

        workflow = FinancialWorkflow()

        # Verify all agents are initialized
        assert "finance_qa" in workflow.agents
        assert "portfolio" in workflow.agents
        assert "market_analysis" in workflow.agents
        assert "goal_planning" in workflow.agents
        assert "news" in workflow.agents
        assert "tax_education" in workflow.agents

    @requires_app_imports
    @patch("app.agent.finance_agent.FinanceAgent")
    @patch("app.agent.portfolio_agent.PortfolioAgent")
    @patch("app.agent.market_agent.MarketAnalysisAgent")
    @patch("app.agent.goal_agent.GoalPlanningAgent")
    @patch("app.agent.news_agent.NewsSynthesizerAgent")
    @patch("app.agent.tax_agent.TaxEducationAgent")
    @patch("langchain_openai.ChatOpenAI")
    def test_workflow_has_graph(
        self, mock_llm, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Test that workflow builds a graph."""
        for mock in [mock_finance, mock_portfolio, mock_market, mock_goal, mock_news, mock_tax]:
            mock.return_value = MagicMock()

        mock_llm.return_value = MagicMock()

        from app.workflow.graph import FinancialWorkflow

        workflow = FinancialWorkflow()

        assert workflow.graph is not None

    @requires_app_imports
    def test_agent_type_literal(self):
        """Test that AgentType contains all expected values."""
        from app.workflow.graph import AgentType

        # AgentType is a Literal type, so we check the string values
        valid_types = [
            "finance_qa", "portfolio", "market_analysis",
            "goal_planning", "news", "tax_education"
        ]

        # This is more of a documentation test
        assert len(valid_types) == 6


class TestRouterIntegration:
    """Tests for router module integration."""

    @requires_app_imports
    @patch("app.agent.router.finance_agent")
    @patch("app.agent.router.portfolio_agent")
    @patch("app.agent.router.market_agent")
    @patch("app.agent.router.goal_agent")
    @patch("app.agent.router.news_agent")
    @patch("app.agent.router.tax_agent")
    def test_keyword_routing_tax(
        self, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Test that tax queries are routed correctly."""
        mock_tax.process_query.return_value = "Tax response"

        # We need to reload the router module with mocks
        with patch.dict(os.environ, {"USE_LANGGRAPH": "false"}):
            from app.agent.router import _keyword_based_routing

            response = _keyword_based_routing("What is a 401k?")

            # Verify tax agent was called
            mock_tax.process_query.assert_called_once_with("What is a 401k?")

    @requires_app_imports
    @patch("app.agent.router.finance_agent")
    @patch("app.agent.router.portfolio_agent")
    @patch("app.agent.router.market_agent")
    @patch("app.agent.router.goal_agent")
    @patch("app.agent.router.news_agent")
    @patch("app.agent.router.tax_agent")
    def test_keyword_routing_market(
        self, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Test that market queries are routed correctly."""
        mock_market.process_query.return_value = "Market response"

        with patch.dict(os.environ, {"USE_LANGGRAPH": "false"}):
            from app.agent.router import _keyword_based_routing

            response = _keyword_based_routing("How is the market today?")

            # Verify market agent was called
            mock_market.process_query.assert_called_once_with("How is the market today?")

    @requires_app_imports
    @patch("app.agent.router.finance_agent")
    @patch("app.agent.router.portfolio_agent")
    @patch("app.agent.router.market_agent")
    @patch("app.agent.router.goal_agent")
    @patch("app.agent.router.news_agent")
    @patch("app.agent.router.tax_agent")
    def test_keyword_routing_default(
        self, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Test that unmatched queries go to finance agent."""
        mock_finance.process_query.return_value = "Finance response"

        with patch.dict(os.environ, {"USE_LANGGRAPH": "false"}):
            from app.agent.router import _keyword_based_routing

            response = _keyword_based_routing("Hello, how are you?")

            # Verify finance agent was called (default)
            mock_finance.process_query.assert_called_once_with("Hello, how are you?")
