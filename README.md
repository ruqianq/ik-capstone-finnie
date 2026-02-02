# FinnIE – Multi-Agent Personal Financial Advisor

A sophisticated multi-agent system for personal financial advisory, orchestrated using Google Agent Development Kit (ADK) with Phoenix-powered observability, deployed locally via Docker Compose.

## Architecture Overview

FinnIE employs a multi-agent architecture with specialized agents handling different aspects of financial advisory:

### Agent Architecture

```
                    ┌─────────────────┐
                    │  Orchestrator   │
                    │     Agent       │
                    └────────┬────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
        ┌───────▼──────┐ ┌──▼─────────┐ ┌▼──────────────┐
        │   Budget     │ │ Investment │ │     Debt      │
        │   Advisor    │ │  Advisor   │ │   Manager     │
        └──────────────┘ └────────────┘ └───────────────┘
                             │
                    ┌────────▼────────┐
                    │   Financial     │
                    │    Planner      │
                    └─────────────────┘
```

### Specialized Agents

1. **Orchestrator Agent** - Routes user queries to appropriate specialist agents
2. **Budget Advisor** - Helps with budget creation and expense management
3. **Investment Advisor** - Provides investment guidance and portfolio advice
4. **Debt Manager** - Assists with debt management and credit improvement
5. **Financial Planner** - Creates comprehensive financial plans

### Technology Stack

- **Agent Framework**: Google Agent Development Kit (ADK)
- **Observability**: Arize Phoenix
- **API Framework**: FastAPI
- **Deployment**: Docker Compose
- **Language**: Python 3.11+

## Prerequisites

- Docker and Docker Compose
- Google API Key (for GenAI)
- Python 3.11+ (for local development)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ruqianq/ik-capstone-finnie.git
cd ik-capstone-finnie
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Start the System with Docker Compose

```bash
docker-compose up --build
```

This will start:
- **FinnIE API** on http://localhost:8000
- **Phoenix Dashboard** on http://localhost:6006

### 4. Access the System

- **API Documentation**: http://localhost:8000/docs
- **Phoenix Observability**: http://localhost:6006
- **Health Check**: http://localhost:8000/health

## Usage

### API Endpoints

#### 1. Query the Financial Advisor

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How should I budget my monthly income?",
    "user_id": "user123"
  }'
```

#### 2. List Available Agents

```bash
curl http://localhost:8000/agents
```

#### 3. Health Check

```bash
curl http://localhost:8000/health
```

### Example Queries

**Budget Planning:**
```json
{
  "query": "I make $5000 per month. How should I allocate my budget?"
}
```

**Investment Advice:**
```json
{
  "query": "I want to start investing $500 per month. What should I consider?"
}
```

**Debt Management:**
```json
{
  "query": "I have $10,000 in credit card debt. What's the best repayment strategy?"
}
```

**Financial Planning:**
```json
{
  "query": "I'm 30 years old and want to retire at 60. How should I plan?"
}
```

## Development

### Local Development Setup

1. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables:**
```bash
export GOOGLE_API_KEY=your_api_key_here
export PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
```

3. **Run the Application:**
```bash
python -m finnie.main
```

### Project Structure

```
ik-capstone-finnie/
├── finnie/                    # Main application package
│   ├── agents/               # Agent implementations
│   │   ├── base_agent.py    # Base agent class
│   │   ├── orchestrator.py  # Orchestrator agent
│   │   └── __init__.py
│   ├── utils/               # Utility modules
│   │   ├── config.py        # Configuration management
│   │   ├── observability.py # Phoenix integration
│   │   └── __init__.py
│   ├── main.py              # Application entry point
│   └── __init__.py
├── config/                   # Configuration files
│   └── agents.json          # Agent configurations
├── tests/                    # Test suite
├── docker/                   # Docker-related files
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile               # Container definition
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Observability

### Phoenix Dashboard

The Phoenix dashboard provides comprehensive observability:

1. **Trace Visualization**: See the complete flow of queries through the agent system
2. **Performance Metrics**: Monitor response times and throughput
3. **Agent Analytics**: Analyze which agents are handling what types of queries
4. **Error Tracking**: Identify and debug issues in real-time

Access the dashboard at http://localhost:6006

## Configuration

### Agent Configuration

Agents are configured in `config/agents.json`:

```json
{
  "agents": {
    "agent_name": {
      "name": "Display Name",
      "description": "Agent description",
      "model": "gemini-1.5-flash",
      "system_prompt": "Agent instructions..."
    }
  }
}
```

### Environment Variables

- `GOOGLE_API_KEY`: Your Google API key for GenAI
- `PHOENIX_COLLECTOR_ENDPOINT`: Phoenix collector endpoint
- `APP_HOST`: Application host (default: 0.0.0.0)
- `APP_PORT`: Application port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)

## Testing

Run the test suite:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest tests/ --cov=finnie --cov-report=html
```

## Docker Deployment

### Building the Image

```bash
docker build -t finnie:latest .
```

### Running with Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Security Considerations

- Never commit your `.env` file or API keys
- Use environment variables for sensitive configuration
- Implement rate limiting for production deployments
- Add authentication/authorization for production use
- Regularly update dependencies for security patches

## Disclaimer

FinnIE provides educational financial information and should not be considered as professional financial advice. Users should consult with qualified financial advisors for personalized financial planning.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the GitHub repository.