"""Orchestrator agent for routing queries to specialized agents."""
import json
from typing import Dict, Any, List
from .base_agent import FinancialAgent


class OrchestratorAgent(FinancialAgent):
    """Orchestrator agent that routes queries to appropriate specialists."""
    
    def __init__(self, name: str, config: Dict[str, Any], api_key: str, 
                 available_agents: Dict[str, FinancialAgent]):
        """Initialize orchestrator agent.
        
        Args:
            name: Agent name
            config: Agent configuration
            api_key: Google API key
            available_agents: Dictionary of available specialist agents
        """
        super().__init__(name, config, api_key)
        self.available_agents = available_agents
        
    def _get_agent_descriptions(self) -> str:
        """Get descriptions of all available agents.
        
        Returns:
            Formatted string of agent descriptions
        """
        descriptions = []
        for agent_name, agent in self.available_agents.items():
            info = agent.get_info()
            descriptions.append(f"- {agent_name}: {info['description']}")
        return "\n".join(descriptions)
    
    async def route_query(self, user_query: str) -> Dict[str, Any]:
        """Route user query to appropriate agent(s).
        
        Args:
            user_query: User's question or request
            
        Returns:
            Dictionary with routing decision and response
        """
        # Ask the orchestrator to determine which agent should handle the query
        routing_prompt = f"""
{self.system_prompt}

Available agents:
{self._get_agent_descriptions()}

Based on the user's query, determine which agent(s) should handle it.
Respond ONLY with a JSON object in this format:
{{
    "primary_agent": "agent_name",
    "reasoning": "brief explanation"
}}

User Query: {user_query}
"""
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=routing_prompt
        )
        
        # Parse the routing decision
        try:
            # Extract JSON from response
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
                
            routing_decision = json.loads(response_text)
            agent_name = routing_decision.get("primary_agent", "financial_planner")
            reasoning = routing_decision.get("reasoning", "")
        except (json.JSONDecodeError, IndexError, AttributeError):
            # Fallback to financial planner if parsing fails
            agent_name = "financial_planner"
            reasoning = "Using default agent due to routing error"
        
        # Route to the selected agent
        if agent_name in self.available_agents:
            selected_agent = self.available_agents[agent_name]
            agent_response = await selected_agent.process(user_query)
        else:
            # Fallback to financial planner
            selected_agent = self.available_agents.get("financial_planner")
            if selected_agent:
                agent_response = await selected_agent.process(user_query)
            else:
                agent_response = "I apologize, but I couldn't route your query to an appropriate agent."
        
        return {
            "routed_to": agent_name,
            "reasoning": reasoning,
            "response": agent_response,
            "agent_info": selected_agent.get_info() if agent_name in self.available_agents else {}
        }
