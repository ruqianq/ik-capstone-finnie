from opentelemetry import trace

from app.agent.finance_agent import FinanceAgent

tracer = trace.get_tracer(__name__)
finance_agent = FinanceAgent()

def route_and_process(user_input: str) -> str:
    """
    Routes user input to the appropriate agent.
    """
    # Simple routing logic for Phase 2: Everything goes to Finance Agent
    # In Phase 3, we can add intent classification here
    
    response = finance_agent.process_query(user_input)
    return response
