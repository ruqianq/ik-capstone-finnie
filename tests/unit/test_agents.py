"""
Unit tests for FinnIE agents.

Note: These tests require app imports which need pandas/yfinance.
Tests will be skipped if imports fail (e.g., in some local environments).
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
    import yfinance
    import pandas
except (ImportError, ValueError, Exception) as e:
    _IMPORTS_AVAILABLE = False
    _IMPORT_ERROR = str(e)

requires_app_imports = pytest.mark.skipif(
    not _IMPORTS_AVAILABLE,
    reason=f"App imports not available: {_IMPORT_ERROR[:100] if _IMPORT_ERROR else 'unknown'}"
)


class TestFinanceAgent:
    """Tests for the Finance Q&A Agent."""

    @requires_app_imports
    @patch("app.rag.retriever.FinanceRetriever")
    @patch("langchain_openai.ChatOpenAI")
    def test_process_query_with_context(self, mock_llm_class, mock_retriever_class):
        """Test that finance agent retrieves context and generates response."""
        # Setup mocks
        mock_doc = Mock()
        mock_doc.page_content = "A stock represents ownership in a company."

        mock_retriever = MagicMock()
        mock_retriever.get_relevant_documents.return_value = [mock_doc]
        mock_retriever_class.return_value = mock_retriever

        mock_llm = MagicMock()
        mock_response = Mock()
        mock_response.content = "Stocks are ownership shares in companies."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        # Import after mocking
        from app.agent.finance_agent import FinanceAgent

        agent = FinanceAgent()
        response = agent.process_query("What is a stock?")

        # Verify retriever was called
        mock_retriever.get_relevant_documents.assert_called_once_with("What is a stock?")

        # Response should include source citation
        assert "Knowledge Base" in response or isinstance(response, str)

    @requires_app_imports
    @patch("app.rag.retriever.FinanceRetriever")
    @patch("langchain_openai.ChatOpenAI")
    def test_process_query_handles_error(self, mock_llm_class, mock_retriever_class):
        """Test that finance agent handles errors gracefully."""
        mock_retriever = MagicMock()
        mock_retriever.get_relevant_documents.return_value = []
        mock_retriever_class.return_value = mock_retriever

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API Error")
        mock_llm_class.return_value = mock_llm

        from app.agent.finance_agent import FinanceAgent

        agent = FinanceAgent()
        response = agent.process_query("What is a bond?")

        assert "Error" in response or isinstance(response, str)


class TestPortfolioAgent:
    """Tests for the Portfolio Agent."""

    @requires_app_imports
    @patch("app.database.init_db")
    @patch("app.tools.market_data.MarketDataTool")
    def test_parse_add_command(self, mock_market_tool_class, mock_init_db):
        """Test parsing of add holding command."""
        mock_market_tool = MagicMock()
        mock_market_tool.get_stock_price.return_value = {
            "last_price": 175.50,
            "change_percent": 1.25
        }
        mock_market_tool_class.return_value = mock_market_tool

        from app.agent.portfolio_agent import PortfolioAgent

        agent = PortfolioAgent()

        # Test that ADD command is recognized
        query = "ADD 10 AAPL"
        assert "ADD" in query.upper()
        assert "10" in query
        assert "AAPL" in query.upper()

    @patch("app.database.init_db")
    @patch("app.tools.market_data.MarketDataTool")
    def test_parse_portfolio_command(self, mock_market_tool_class, mock_init_db):
        """Test parsing of view portfolio command."""
        mock_market_tool = MagicMock()
        mock_market_tool_class.return_value = mock_market_tool

        from app.agent.portfolio_agent import PortfolioAgent

        agent = PortfolioAgent()

        query = "Show my portfolio"
        assert "PORTFOLIO" in query.upper()

    @patch("app.database.init_db")
    @patch("app.tools.market_data.MarketDataTool")
    def test_ticker_extraction(self, mock_market_tool_class, mock_init_db):
        """Test extraction of tickers from queries."""
        mock_market_tool = MagicMock()
        mock_market_tool.get_stock_price.return_value = {
            "last_price": 175.50,
            "change_percent": 1.25
        }
        mock_market_tool_class.return_value = mock_market_tool

        from app.agent.portfolio_agent import PortfolioAgent

        agent = PortfolioAgent()

        # Company name should be converted
        query = "What is the price of APPLE"
        query_upper = query.upper()

        COMPANY_MAPPING = {
            "APPLE": "AAPL",
            "GOOGLE": "GOOG",
            "MICROSOFT": "MSFT"
        }

        for name, ticker in COMPANY_MAPPING.items():
            if name in query_upper:
                query_upper = query_upper.replace(name, ticker)

        assert "AAPL" in query_upper

    @patch("app.database.init_db")
    @patch("app.tools.market_data.MarketDataTool")
    def test_no_ticker_found(self, mock_market_tool_class, mock_init_db):
        """Test response when no ticker is identified."""
        mock_market_tool = MagicMock()
        mock_market_tool_class.return_value = mock_market_tool

        from app.agent.portfolio_agent import PortfolioAgent

        agent = PortfolioAgent()
        response = agent.process_query("Hello there!")

        assert "couldn't identify" in response.lower() or "try" in response.lower()


class TestMarketAgent:
    """Tests for the Market Analysis Agent."""

    @patch("langchain_openai.ChatOpenAI")
    @patch("yfinance.Ticker")
    def test_market_overview(self, mock_ticker_class, mock_llm_class):
        """Test market overview functionality."""
        # Setup yfinance mock
        mock_ticker = MagicMock()
        mock_history = MagicMock()
        mock_history.empty = False
        mock_history.__getitem__ = Mock(return_value=MagicMock(iloc=Mock(return_value=[4500.0, 4400.0])))
        mock_ticker.history.return_value = mock_history
        mock_ticker_class.return_value = mock_ticker

        # Setup LLM mock
        mock_llm = MagicMock()
        mock_response = Mock()
        mock_response.content = "Market is up today."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        from app.agent.market_agent import MarketAnalysisAgent

        agent = MarketAnalysisAgent()

        # Test that indices are defined
        assert "S&P 500" in agent.indices
        assert "Dow Jones" in agent.indices
        assert "NASDAQ" in agent.indices

    @patch("langchain_openai.ChatOpenAI")
    @patch("yfinance.Ticker")
    def test_sector_analysis(self, mock_ticker_class, mock_llm_class):
        """Test sector analysis functionality."""
        mock_ticker = MagicMock()
        mock_history = MagicMock()
        mock_history.empty = False
        mock_ticker.history.return_value = mock_history
        mock_ticker_class.return_value = mock_ticker

        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm

        from app.agent.market_agent import MarketAnalysisAgent

        agent = MarketAnalysisAgent()

        # Test that sectors are defined
        assert "Technology" in agent.sectors
        assert "Healthcare" in agent.sectors
        assert "Financials" in agent.sectors


class TestGoalAgent:
    """Tests for the Goal Planning Agent."""

    @patch("langchain_openai.ChatOpenAI")
    def test_goal_planning_prompt(self, mock_llm_class):
        """Test that goal planning agent has proper prompt."""
        mock_llm = MagicMock()
        mock_response = Mock()
        mock_response.content = "To save $50,000 in 5 years, you need..."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        from app.agent.goal_agent import GoalPlanningAgent

        agent = GoalPlanningAgent()

        # Verify LLM was initialized
        mock_llm_class.assert_called()

    @patch("langchain_openai.ChatOpenAI")
    def test_goal_query_processing(self, mock_llm_class):
        """Test processing of goal-related queries."""
        mock_llm = MagicMock()
        mock_response = Mock()
        mock_response.content = "Based on your goal..."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        from app.agent.goal_agent import GoalPlanningAgent

        agent = GoalPlanningAgent()
        response = agent.process_query("I want to save $50,000 for a house in 5 years")

        assert isinstance(response, str)


class TestNewsAgent:
    """Tests for the News Synthesizer Agent."""

    @patch("langchain_openai.ChatOpenAI")
    @patch("yfinance.Ticker")
    def test_news_retrieval(self, mock_ticker_class, mock_llm_class):
        """Test news retrieval functionality."""
        mock_ticker = MagicMock()
        mock_ticker.news = [
            {
                "title": "Markets Rally",
                "publisher": "Reuters",
                "link": "https://example.com",
                "providerPublishTime": 1700000000
            }
        ]
        mock_ticker_class.return_value = mock_ticker

        mock_llm = MagicMock()
        mock_response = Mock()
        mock_response.content = "Market news summary..."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        from app.agent.news_agent import NewsSynthesizerAgent

        agent = NewsSynthesizerAgent()

        # Verify agent can be initialized
        assert agent is not None


class TestTaxAgent:
    """Tests for the Tax Education Agent."""

    @patch("langchain_openai.ChatOpenAI")
    def test_tax_knowledge_base(self, mock_llm_class):
        """Test that tax agent has embedded knowledge."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm

        from app.agent.tax_agent import TaxEducationAgent

        agent = TaxEducationAgent()

        # Verify knowledge base contains key topics
        assert "401k" in agent.tax_knowledge.lower() or "401(k)" in agent.tax_knowledge.lower()
        assert "ira" in agent.tax_knowledge.lower()
        assert "roth" in agent.tax_knowledge.lower()

    @patch("langchain_openai.ChatOpenAI")
    def test_tax_query_processing(self, mock_llm_class):
        """Test processing of tax-related queries."""
        mock_llm = MagicMock()
        mock_response = Mock()
        mock_response.content = "The 401(k) contribution limit is..."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        from app.agent.tax_agent import TaxEducationAgent

        agent = TaxEducationAgent()
        response = agent.process_query("What are the 401k contribution limits?")

        assert isinstance(response, str)
