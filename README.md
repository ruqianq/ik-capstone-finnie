# FinnIE – Multi-Agent Personal Financial Advisor 💰

FinnIE is an intelligent multi-agent system for personal financial advice, built with Google Agent Development Kit (ADK), featuring Phoenix-powered observability and deployed locally via Docker Compose.

## 🌟 Features

- **Multi-Agent Architecture**: Specialized agents for different financial domains
  - Finance Q&A Agent (RAG-backed)
  - Portfolio Analysis Agent
  - Market Analysis Agent
  - Goal Planning Agent

- **Retrieval-Augmented Generation (RAG)**: FAISS-powered vector search for accurate financial information

- **Comprehensive Observability**: OpenTelemetry + Phoenix for full request tracing

- **Modern UI**: Streamlit-based interface with multiple tabs for different functionalities

- **Robust Tools**: Caching, retry logic, and rate limiting for external APIs

## 🏗️ Architecture

```
User → Streamlit UI
     → ADK Router (Intent Classification)
       → Specialized Agent(s)
         → RAG / Tools / APIs
           → LLM
     → Response + Trace ID
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- OpenAI API key (optional, for LLM integration)

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/ruqianq/ik-capstone-finnie.git
cd ik-capstone-finnie
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Start the services:
```bash
docker-compose up -d
```

4. Access the application:
   - FinnIE UI: http://localhost:8501
   - Phoenix Observability: http://localhost:6006

### Local Development

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
streamlit run finnie/ui/app.py
```

## 🧪 Testing

Run tests with coverage:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/agents/test_router.py
```

Check coverage:
```bash
pytest --cov=finnie --cov-report=html
```

## 📁 Project Structure

```
ik-capstone-finnie/
├── finnie/                    # Main application package
│   ├── agents/               # Agent implementations
│   │   ├── base.py          # Base agent interface
│   │   ├── router.py        # ADK router for orchestration
│   │   ├── finance_qa.py    # Finance Q&A agent
│   │   ├── portfolio.py     # Portfolio analysis agent
│   │   ├── market.py        # Market analysis agent
│   │   └── goals.py         # Goal planning agent
│   ├── rag/                 # RAG pipeline
│   │   └── pipeline.py      # FAISS-based retrieval
│   ├── tools/               # Tool wrappers
│   │   ├── base.py          # Caching, rate limiting, retry
│   │   └── market_data.py   # Market data APIs
│   ├── observability/       # Tracing and monitoring
│   │   └── tracing.py       # OpenTelemetry integration
│   ├── config/              # Configuration management
│   │   └── settings.py      # App configuration
│   └── ui/                  # User interface
│       └── app.py           # Streamlit application
├── tests/                    # Test suite
│   ├── agents/              # Agent tests
│   ├── rag/                 # RAG tests
│   └── tools/               # Tool tests
├── data/                     # Data storage
│   ├── articles/            # Financial articles
│   └── glossary/            # Financial glossary
├── docker-compose.yml        # Docker composition
├── Dockerfile               # Application container
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🎯 Core Components

### 1. Agent Framework (Google ADK)

Each agent implements a standard interface with:
- Independent testability
- Structured trace emission
- Deterministic behavior
- Request validation

### 2. Orchestration & Routing

- Intent classification at request entry
- Deterministic routing to appropriate agents
- Support for multi-agent chaining (future)

### 3. RAG Pipeline

- **Vector Store**: FAISS (local)
- **Data**: Financial articles and glossary
- **Pipeline**: Chunk → Embed → Index → Retrieve
- **Citations**: Returned with responses for transparency

### 4. Tools & External Integrations

- Market data APIs (yFinance, Alpha Vantage)
- Tool features:
  - TTL-based caching
  - Retry with exponential backoff
  - Rate-limit protection

### 5. Observability

- **Tracing**: OpenTelemetry
- **Backend**: Phoenix
- **Coverage**:
  - Request lifecycle
  - Router decisions
  - Agent execution
  - RAG retrieval
  - Tool/API calls
  - LLM invocations

### 6. User Interface

- Framework: Streamlit
- Tabs:
  - Chat: Interactive Q&A
  - Portfolio: Portfolio analysis
  - Market: Market data and trends
  - Goals: Financial planning
- Trace ID displayed per interaction

## 🔧 Configuration

Edit `.env` file to configure:

```bash
# LLM Configuration
OPENAI_API_KEY=your_key_here

# Market Data APIs
ALPHA_VANTAGE_API_KEY=your_key_here
YFINANCE_ENABLED=true

# Observability
PHOENIX_HOST=phoenix
PHOENIX_PORT=6006

# RAG Configuration
FAISS_INDEX_PATH=/app/faiss_data
TOP_K_RESULTS=5

# Cache Configuration
CACHE_TTL=3600
RATE_LIMIT_CALLS=60
```

## 📊 Non-Functional Requirements

- ✅ Modular and extensible agent design
- ✅ Deterministic, explainable behavior
- ✅ Fault tolerance for API failures
- ✅ ≥80% unit test coverage for core logic
- ✅ OpenTelemetry tracing for all operations
- ✅ Docker-based deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure tests pass: `pytest`
6. Submit a pull request

## 📝 License

This project is part of the IK Capstone program.

## 🙏 Acknowledgments

- Google Agent Development Kit (ADK)
- Phoenix for observability
- Streamlit for the UI framework
- FAISS for vector search
- OpenTelemetry for tracing

## 📞 Support

For issues and questions, please open an issue on GitHub.