"""
Pytest configuration and fixtures for FinnIE tests.
"""

import os
import sys
import pytest
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment variables before importing app modules
os.environ["OPENAI_API_KEY"] = "test-api-key"
os.environ["USE_LANGGRAPH"] = "false"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["EMBEDDING_MODEL"] = "nomic-embed-text"


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = Mock()
    mock_response.content = "This is a mock response from the LLM."
    return mock_response


@pytest.fixture
def mock_chat_openai(mock_openai_response):
    """Mock ChatOpenAI class."""
    with patch("langchain_openai.ChatOpenAI") as mock_class:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = mock_openai_response
        mock_class.return_value = mock_instance
        yield mock_class


@pytest.fixture
def mock_yfinance_ticker():
    """Mock yfinance Ticker for market data."""
    with patch("yfinance.Ticker") as mock_ticker:
        mock_instance = MagicMock()

        # Mock stock info
        mock_instance.info = {
            "symbol": "AAPL",
            "shortName": "Apple Inc.",
            "currentPrice": 175.50,
            "previousClose": 174.00,
            "marketCap": 2800000000000,
            "fiftyTwoWeekHigh": 199.62,
            "fiftyTwoWeekLow": 124.17,
        }

        # Mock history
        mock_history = MagicMock()
        mock_history.empty = False
        mock_history.__getitem__ = Mock(return_value=MagicMock(iloc=Mock(return_value=175.50)))
        mock_instance.history.return_value = mock_history

        # Mock news
        mock_instance.news = [
            {
                "title": "Apple Reports Strong Earnings",
                "publisher": "Reuters",
                "link": "https://example.com/news1",
                "providerPublishTime": 1700000000,
            },
            {
                "title": "Tech Stocks Rally",
                "publisher": "Bloomberg",
                "link": "https://example.com/news2",
                "providerPublishTime": 1699999000,
            },
        ]

        mock_ticker.return_value = mock_instance
        yield mock_ticker


@pytest.fixture
def mock_faiss_retriever():
    """Mock FAISS vector store retriever."""
    with patch("langchain_community.vectorstores.FAISS") as mock_faiss:
        mock_instance = MagicMock()

        # Mock document retrieval
        mock_doc = Mock()
        mock_doc.page_content = "A stock represents ownership in a company."
        mock_doc.metadata = {"source": "test_doc.md"}

        mock_instance.similarity_search.return_value = [mock_doc]
        mock_instance.as_retriever.return_value = MagicMock()
        mock_faiss.load_local.return_value = mock_instance

        yield mock_faiss


@pytest.fixture
def mock_ollama_embeddings():
    """Mock Ollama embeddings."""
    with patch("langchain_ollama.OllamaEmbeddings") as mock_embeddings:
        mock_instance = MagicMock()
        mock_instance.embed_query.return_value = [0.1] * 768
        mock_instance.embed_documents.return_value = [[0.1] * 768]
        mock_embeddings.return_value = mock_instance
        yield mock_embeddings


@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing."""
    return [
        {"symbol": "AAPL", "shares": 10, "avg_price": 150.00},
        {"symbol": "MSFT", "shares": 5, "avg_price": 350.00},
        {"symbol": "GOOGL", "shares": 3, "avg_price": 140.00},
    ]


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "S&P 500": {"price": 4500.00, "change": 0.75},
        "Dow Jones": {"price": 35000.00, "change": 0.50},
        "NASDAQ": {"price": 14000.00, "change": 1.25},
    }


@pytest.fixture
def temp_database(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_portfolio.db"
    os.environ["DATABASE_PATH"] = str(db_path)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def mock_tracer():
    """Mock OpenTelemetry tracer."""
    with patch("opentelemetry.trace.get_tracer") as mock_get_tracer:
        mock_tracer_instance = MagicMock()
        mock_span = MagicMock()
        mock_span.__enter__ = Mock(return_value=mock_span)
        mock_span.__exit__ = Mock(return_value=None)
        mock_tracer_instance.start_as_current_span.return_value = mock_span
        mock_get_tracer.return_value = mock_tracer_instance
        yield mock_tracer_instance
