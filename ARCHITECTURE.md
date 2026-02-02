# FinnIE Architecture Documentation

## System Overview

FinnIE (Financial Intelligence Engine) is a multi-agent personal financial advisor system built using Google's Agent Development Kit (ADK) and Phoenix observability platform.

## Architecture Components

### 1. Multi-Agent System

```
┌─────────────────────────────────────────────────────────────┐
│                      FinnIE System                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Orchestrator Agent                      │  │
│  │  (Routes queries to appropriate specialists)         │  │
│  └───────────────┬──────────────────────────────────────┘  │
│                  │                                          │
│         ┌────────┼────────┬──────────┬─────────────┐       │
│         │        │        │          │             │       │
│  ┌──────▼────┐ ┌▼────────▼─┐  ┌─────▼──────┐  ┌──▼─────┐ │
│  │  Budget   │ │ Investment │  │   Debt     │  │Financial│ │
│  │  Advisor  │ │  Advisor   │  │  Manager   │  │ Planner │ │
│  └───────────┘ └────────────┘  └────────────┘  └─────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   FastAPI    │  │  Pydantic    │  │  Structlog   │     │
│  │  (REST API)  │  │ (Validation) │  │  (Logging)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                    Agent Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Google GenAI │  │  Orchestrator│  │  Specialist  │     │
│  │     SDK      │  │    Agent     │  │   Agents     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                  Observability Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Phoenix    │  │     OTEL     │  │   Tracing    │     │
│  │  Dashboard   │  │   (OpenTel)  │  │   & Metrics  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 3. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Phoenix Container                       │  │
│  │  Image: arizephoenix/phoenix:latest                 │  │
│  │  Port: 6006                                          │  │
│  │  - Observability Dashboard                           │  │
│  │  - Trace Collection                                  │  │
│  │  - Metrics & Analytics                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↑                                   │
│                         │ (traces)                          │
│                         │                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              FinnIE Container                        │  │
│  │  Image: Built from Dockerfile                        │  │
│  │  Port: 8000                                          │  │
│  │  - FastAPI Application                               │  │
│  │  - Multi-Agent System                                │  │
│  │  - Agent Orchestration                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │                               │
         │ (API)                         │ (Dashboard)
         ↓                               ↓
    localhost:8000                  localhost:6006
```

## Data Flow

### Query Processing Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │
     │ 1. Submit Query
     ↓
┌─────────────────┐
│   FastAPI       │
│   Endpoint      │
│   /query        │
└────┬────────────┘
     │
     │ 2. Forward to Orchestrator
     ↓
┌─────────────────┐
│  Orchestrator   │
│     Agent       │◄──── Phoenix Tracing
└────┬────────────┘
     │
     │ 3. Route Query
     ├─────┬─────┬─────┬─────┐
     ↓     ↓     ↓     ↓     ↓
  ┌──────┬──────┬──────┬──────┐
  │Budget│Invest│ Debt │Fin.  │
  │Advsr │Advsr │Mgr   │Plan. │
  └──┬───┴───┬──┴───┬──┴───┬──┘
     │       │      │      │
     │ 4. Process with Google GenAI
     │       │      │      │
     └───────┴──────┴──────┘
             │
             │ 5. Return Response
             ↓
        ┌─────────┐
        │  User   │
        └─────────┘
```

## Agent Roles and Responsibilities

### Orchestrator Agent
- **Purpose**: Route queries to appropriate specialist agents
- **Model**: gemini-1.5-pro (more powerful for routing decisions)
- **Responsibilities**:
  - Analyze user queries
  - Determine appropriate agent(s)
  - Coordinate multi-agent responses
  - Return unified response to user

### Budget Advisor
- **Purpose**: Budget creation and expense management
- **Model**: gemini-1.5-flash
- **Responsibilities**:
  - Create budget plans
  - Track expenses
  - Provide saving strategies
  - Analyze spending patterns

### Investment Advisor
- **Purpose**: Investment guidance
- **Model**: gemini-1.5-flash
- **Responsibilities**:
  - Explain investment options
  - Portfolio diversification advice
  - Risk management guidance
  - Educational investment information

### Debt Manager
- **Purpose**: Debt management strategies
- **Model**: gemini-1.5-flash
- **Responsibilities**:
  - Debt repayment strategies
  - Interest rate analysis
  - Credit score improvement
  - Debt consolidation advice

### Financial Planner
- **Purpose**: Comprehensive financial planning
- **Model**: gemini-1.5-flash
- **Responsibilities**:
  - Long-term financial goals
  - Life event planning
  - Retirement planning
  - Overall financial strategy coordination

## Security Architecture

### API Security
```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                          │
│                                                             │
│  1. Environment Variables                                   │
│     └─ API keys stored in .env (not committed)             │
│                                                             │
│  2. Docker Network Isolation                                │
│     └─ Services communicate on internal network            │
│                                                             │
│  3. Input Validation                                        │
│     └─ Pydantic models validate all inputs                 │
│                                                             │
│  4. Rate Limiting (Recommended for Production)              │
│     └─ Protect against abuse                               │
│                                                             │
│  5. HTTPS/TLS (Recommended for Production)                  │
│     └─ Encrypt all communications                          │
└─────────────────────────────────────────────────────────────┘
```

## Observability Architecture

### Phoenix Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    Phoenix Observability                     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Trace Collection                        │  │
│  │  - Request traces                                    │  │
│  │  - Agent execution traces                            │  │
│  │  - LLM call traces                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Metrics & Analytics                     │  │
│  │  - Response times                                    │  │
│  │  - Agent routing patterns                            │  │
│  │  - Error rates                                       │  │
│  │  - Token usage                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Visualization                           │  │
│  │  - Real-time dashboards                              │  │
│  │  - Query flow diagrams                               │  │
│  │  - Performance graphs                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Configuration Management

### Configuration Hierarchy

```
config/
└── agents.json
    ├── system
    │   ├── name
    │   ├── version
    │   └── description
    ├── observability
    │   ├── phoenix_endpoint
    │   ├── enable_tracing
    │   └── enable_logging
    └── agents
        ├── budget_advisor
        ├── investment_advisor
        ├── debt_manager
        ├── financial_planner
        └── orchestrator
```

## Scalability Considerations

### Horizontal Scaling

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                            │
│                   (e.g., Nginx)                             │
└────────────┬─────────────┬─────────────┬────────────────────┘
             │             │             │
      ┌──────▼──────┐ ┌────▼─────┐ ┌────▼─────┐
      │  FinnIE     │ │  FinnIE  │ │  FinnIE  │
      │ Instance 1  │ │Instance 2│ │Instance 3│
      └──────┬──────┘ └────┬─────┘ └────┬─────┘
             │             │             │
             └─────────────┴─────────────┘
                          │
                    ┌─────▼──────┐
                    │  Shared    │
                    │  Phoenix   │
                    └────────────┘
```

### Vertical Scaling

- Increase container resources (CPU, Memory)
- Optimize model selection (flash vs pro)
- Implement caching for common queries
- Add request queuing

## Extension Points

### Adding New Agents

1. Define agent configuration in `config/agents.json`
2. Agent automatically loaded on startup
3. Orchestrator learns new agent capabilities
4. No code changes required for simple agents

### Custom Agent Implementation

1. Extend `FinancialAgent` base class
2. Override `process()` method for custom logic
3. Register in agent initialization
4. Update orchestrator awareness

### Adding New Features

- **User Authentication**: Add middleware to FastAPI
- **Data Persistence**: Add database layer
- **Caching**: Integrate Redis
- **API Gateway**: Add Kong or similar
- **Message Queue**: Add RabbitMQ/Kafka for async processing

## Performance Considerations

### Response Time Optimization

1. **Model Selection**:
   - Use flash models for specialist agents (faster)
   - Use pro models only for orchestration (more accurate)

2. **Caching**:
   - Cache common queries
   - Cache agent routing decisions

3. **Async Processing**:
   - All agent calls are async
   - Parallel agent consultation when needed

4. **Resource Limits**:
   - Set appropriate Docker resource limits
   - Monitor and adjust based on load

## Monitoring Checklist

- [ ] API response times < 5s for 95th percentile
- [ ] Phoenix traces successfully captured
- [ ] Error rate < 1%
- [ ] Agent routing accuracy > 90%
- [ ] Container resource usage within limits
- [ ] No memory leaks over time
- [ ] Log aggregation working
- [ ] Health checks passing

## Future Enhancements

1. **Multi-tenancy**: Support multiple users with isolated data
2. **Conversation History**: Maintain context across queries
3. **Personalization**: Learn user preferences over time
4. **Integration**: Connect to financial data sources (Plaid, etc.)
5. **Advanced Analytics**: ML-based insights and predictions
6. **Mobile App**: Native mobile interface
7. **Voice Interface**: Voice-based interaction
8. **Multi-language**: Support multiple languages
