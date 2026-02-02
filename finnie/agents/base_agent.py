"""Base agent class for FinnIE system."""
import json
from typing import Dict, Any, Optional
from google import genai
from google.genai import types


class FinancialAgent:
    """Base class for financial advisory agents."""
    
    def __init__(self, name: str, config: Dict[str, Any], api_key: str):
        """Initialize the agent.
        
        Args:
            name: Agent name
            config: Agent configuration
            api_key: Google API key
        """
        self.name = name
        self.config = config
        self.model_name = config.get("model", "gemini-1.5-flash")
        self.system_prompt = config.get("system_prompt", "")
        
        # Initialize Google GenAI client
        self.client = genai.Client(api_key=api_key)
        
    async def process(self, user_query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process user query and return response.
        
        Args:
            user_query: User's question or request
            context: Optional context information
            
        Returns:
            Agent's response
        """
        # Build the full prompt
        prompt = f"{self.system_prompt}\n\nUser Query: {user_query}"
        
        if context:
            prompt += f"\n\nContext: {json.dumps(context, indent=2)}"
        
        # Generate response using Google GenAI
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        
        return response.text
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information.
        
        Returns:
            Dictionary with agent information
        """
        return {
            "name": self.name,
            "description": self.config.get("description", ""),
            "model": self.model_name
        }
