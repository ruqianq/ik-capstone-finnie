"""Tests for configuration management."""
import pytest
import json
from pathlib import Path
from finnie.utils.config import ConfigManager


def test_config_manager_initialization(tmp_path):
    """Test ConfigManager initialization."""
    # Create a temporary config file
    config_file = tmp_path / "test_config.json"
    config_data = {
        "system": {
            "name": "FinnIE",
            "version": "1.0.0"
        },
        "agents": {
            "test_agent": {
                "name": "Test Agent",
                "model": "gemini-1.5-flash"
            }
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    # Test initialization
    config_manager = ConfigManager(str(config_file))
    assert config_manager.config is not None
    assert config_manager.get_system_config()["name"] == "FinnIE"


def test_get_system_config(tmp_path):
    """Test getting system configuration."""
    config_file = tmp_path / "test_config.json"
    config_data = {
        "system": {
            "name": "FinnIE",
            "version": "1.0.0",
            "description": "Test system"
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    config_manager = ConfigManager(str(config_file))
    system_config = config_manager.get_system_config()
    
    assert system_config["name"] == "FinnIE"
    assert system_config["version"] == "1.0.0"
    assert system_config["description"] == "Test system"


def test_get_agent_config(tmp_path):
    """Test getting agent configuration."""
    config_file = tmp_path / "test_config.json"
    config_data = {
        "agents": {
            "budget_advisor": {
                "name": "Budget Advisor",
                "model": "gemini-1.5-flash",
                "system_prompt": "Test prompt"
            }
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    config_manager = ConfigManager(str(config_file))
    agent_config = config_manager.get_agent_config("budget_advisor")
    
    assert agent_config["name"] == "Budget Advisor"
    assert agent_config["model"] == "gemini-1.5-flash"


def test_get_all_agents_config(tmp_path):
    """Test getting all agents configuration."""
    config_file = tmp_path / "test_config.json"
    config_data = {
        "agents": {
            "agent1": {"name": "Agent 1"},
            "agent2": {"name": "Agent 2"}
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    config_manager = ConfigManager(str(config_file))
    all_agents = config_manager.get_all_agents_config()
    
    assert len(all_agents) == 2
    assert "agent1" in all_agents
    assert "agent2" in all_agents


def test_config_file_not_found():
    """Test error handling when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        ConfigManager("/nonexistent/path/config.json")
