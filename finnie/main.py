"""Main application entry point for FinnIE."""
import os
import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from finnie.agents import FinancialAgent, OrchestratorAgent
from finnie.utils import ConfigManager, PhoenixObservability


# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FinnIE - Multi-Agent Personal Financial Advisor",
    description="A multi-agent system for personal financial advisory powered by Google ADK",
    version="1.0.0"
)


class QueryRequest(BaseModel):
    """Request model for financial queries."""
    query: str
    user_id: str = "anonymous"


class QueryResponse(BaseModel):
    """Response model for financial queries."""
    query: str
    routed_to: str
    reasoning: str
    response: str
    agent_info: dict


# Global variables for agent system
config_manager = None
orchestrator = None
observability = None


@app.on_event("startup")
async def startup_event():
    """Initialize the agent system on startup."""
    global config_manager, orchestrator, observability
    
    logger.info("Starting FinnIE system")
    
    # Initialize configuration
    config_manager = ConfigManager()
    system_config = config_manager.get_system_config()
    logger.info("Configuration loaded", system=system_config["name"])
    
    # Initialize observability
    obs_config = config_manager.get_observability_config()
    observability = PhoenixObservability(
        endpoint=obs_config.get("phoenix_endpoint"),
        enable_tracing=obs_config.get("enable_tracing", True)
    )
    observability.setup()
    
    # Get API key from environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY not found in environment")
        raise ValueError("GOOGLE_API_KEY environment variable is required")
    
    # Initialize specialist agents
    agents_config = config_manager.get_all_agents_config()
    specialist_agents = {}
    
    for agent_name, agent_config in agents_config.items():
        if agent_name != "orchestrator":
            agent = FinancialAgent(agent_name, agent_config, api_key)
            specialist_agents[agent_name] = agent
            logger.info(f"Initialized agent: {agent_name}")
    
    # Initialize orchestrator
    orchestrator_config = config_manager.get_agent_config("orchestrator")
    orchestrator = OrchestratorAgent(
        "orchestrator",
        orchestrator_config,
        api_key,
        specialist_agents
    )
    logger.info("Orchestrator initialized")
    
    logger.info("FinnIE system startup complete")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "FinnIE",
        "description": "Multi-Agent Personal Financial Advisor",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "observability": observability.is_initialized() if observability else False
    }


@app.get("/agents")
async def list_agents():
    """List all available agents."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    agents_info = []
    for agent_name, agent in orchestrator.available_agents.items():
        agents_info.append({
            "name": agent_name,
            **agent.get_info()
        })
    
    return {
        "agents": agents_info,
        "orchestrator": orchestrator.get_info()
    }


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a financial query using the multi-agent system.
    
    Args:
        request: Query request containing user query
        
    Returns:
        Query response with agent routing and answer
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    logger.info("Processing query", user_id=request.user_id, query=request.query)
    
    try:
        # Route and process the query
        result = await orchestrator.route_query(request.query)
        
        logger.info(
            "Query processed",
            user_id=request.user_id,
            routed_to=result.get("routed_to")
        )
        
        return QueryResponse(
            query=request.query,
            routed_to=result.get("routed_to", "unknown"),
            reasoning=result.get("reasoning", ""),
            response=result.get("response", ""),
            agent_info=result.get("agent_info", {})
        )
    except Exception as e:
        logger.error("Error processing query", error=str(e), user_id=request.user_id)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    
    uvicorn.run(app, host=host, port=port)
