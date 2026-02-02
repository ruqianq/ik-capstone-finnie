"""Configuration management for FinnIE."""
import json
import os
from typing import Dict, Any
from pathlib import Path


class ConfigManager:
    """Manages configuration for the FinnIE system."""
    
    def __init__(self, config_path: str = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            # Default to config/agents.json
            config_path = Path(__file__).parent.parent.parent / "config" / "agents.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration.
        
        Returns:
            System configuration dictionary
        """
        return self.config.get("system", {})
    
    def get_observability_config(self) -> Dict[str, Any]:
        """Get observability configuration.
        
        Returns:
            Observability configuration dictionary
        """
        return self.config.get("observability", {})
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent configuration dictionary
        """
        agents = self.config.get("agents", {})
        return agents.get(agent_name, {})
    
    def get_all_agents_config(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration for all agents.
        
        Returns:
            Dictionary mapping agent names to their configurations
        """
        return self.config.get("agents", {})
