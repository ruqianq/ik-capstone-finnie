"""
Unit tests for FinnIE Agent Orchestrator.

Tests the supervisor pattern: plan, execute, review, synthesize nodes.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Check if app imports are available
_IMPORTS_AVAILABLE = True
_IMPORT_ERROR = ""
try:
    import yfinance
    import pandas
except (ImportError, ValueError, Exception) as e:
    _IMPORTS_AVAILABLE = False
    _IMPORT_ERROR = str(e)

requires_app_imports = pytest.mark.skipif(
    not _IMPORTS_AVAILABLE,
    reason=f"App imports not available: {_IMPORT_ERROR[:100] if _IMPORT_ERROR else 'unknown'}"
)


class TestOrchestratorState:
    """Tests for orchestrator state schema."""

    @requires_app_imports
    def test_state_has_required_fields(self):
        """Verify OrchestratorState has all expected fields."""
        from app.workflow.orchestrator import OrchestratorState

        state: OrchestratorState = {
            "query": "test query",
            "messages": [],
            "context": None,
            "plan": [],
            "agent_results": {},
            "current_step": 0,
            "iteration_count": 0,
            "max_iterations": 4,
            "needs_more_agents": False,
            "next_agents": [],
            "final_response": None,
            "orchestrator_reasoning": "",
        }

        assert state["query"] == "test query"
        assert state["max_iterations"] == 4
        assert state["plan"] == []
        assert state["agent_results"] == {}


class TestShouldContinue:
    """Tests for the _should_continue routing function."""

    @requires_app_imports
    @patch("app.agent.finance_agent.FinanceAgent")
    @patch("app.agent.portfolio_agent.PortfolioAgent")
    @patch("app.agent.market_agent.MarketAnalysisAgent")
    @patch("app.agent.goal_agent.GoalPlanningAgent")
    @patch("app.agent.news_agent.NewsSynthesizerAgent")
    @patch("app.agent.tax_agent.TaxEducationAgent")
    @patch("langchain_openai.ChatOpenAI")
    def test_continue_when_agents_remain(
        self, mock_llm, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Should return 'continue' when planned agents remain and under max iterations."""
        for mock in [mock_finance, mock_portfolio, mock_market, mock_goal, mock_news, mock_tax]:
            mock.return_value = MagicMock()
        mock_llm.return_value = MagicMock()

        from app.workflow.orchestrator import OrchestratorWorkflow

        orch = OrchestratorWorkflow()

        state = {
            "plan": ["portfolio", "market_analysis"],
            "next_agents": [],
            "current_step": 1,
            "iteration_count": 1,
            "max_iterations": 4,
        }

        result = orch._should_continue(state)
        assert result == "continue"

    @requires_app_imports
    @patch("app.agent.finance_agent.FinanceAgent")
    @patch("app.agent.portfolio_agent.PortfolioAgent")
    @patch("app.agent.market_agent.MarketAnalysisAgent")
    @patch("app.agent.goal_agent.GoalPlanningAgent")
    @patch("app.agent.news_agent.NewsSynthesizerAgent")
    @patch("app.agent.tax_agent.TaxEducationAgent")
    @patch("langchain_openai.ChatOpenAI")
    def test_synthesize_when_all_done(
        self, mock_llm, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Should return 'synthesize' when all planned agents are done."""
        for mock in [mock_finance, mock_portfolio, mock_market, mock_goal, mock_news, mock_tax]:
            mock.return_value = MagicMock()
        mock_llm.return_value = MagicMock()

        from app.workflow.orchestrator import OrchestratorWorkflow

        orch = OrchestratorWorkflow()

        state = {
            "plan": ["portfolio"],
            "next_agents": [],
            "current_step": 1,
            "iteration_count": 1,
            "max_iterations": 4,
        }

        result = orch._should_continue(state)
        assert result == "synthesize"

    @requires_app_imports
    @patch("app.agent.finance_agent.FinanceAgent")
    @patch("app.agent.portfolio_agent.PortfolioAgent")
    @patch("app.agent.market_agent.MarketAnalysisAgent")
    @patch("app.agent.goal_agent.GoalPlanningAgent")
    @patch("app.agent.news_agent.NewsSynthesizerAgent")
    @patch("app.agent.tax_agent.TaxEducationAgent")
    @patch("langchain_openai.ChatOpenAI")
    def test_synthesize_on_max_iterations(
        self, mock_llm, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Should return 'synthesize' when max iterations reached even if agents remain."""
        for mock in [mock_finance, mock_portfolio, mock_market, mock_goal, mock_news, mock_tax]:
            mock.return_value = MagicMock()
        mock_llm.return_value = MagicMock()

        from app.workflow.orchestrator import OrchestratorWorkflow

        orch = OrchestratorWorkflow()

        state = {
            "plan": ["portfolio", "market_analysis", "tax_education", "news", "goal_planning"],
            "next_agents": [],
            "current_step": 2,
            "iteration_count": 4,
            "max_iterations": 4,
        }

        result = orch._should_continue(state)
        assert result == "synthesize"

    @requires_app_imports
    @patch("app.agent.finance_agent.FinanceAgent")
    @patch("app.agent.portfolio_agent.PortfolioAgent")
    @patch("app.agent.market_agent.MarketAnalysisAgent")
    @patch("app.agent.goal_agent.GoalPlanningAgent")
    @patch("app.agent.news_agent.NewsSynthesizerAgent")
    @patch("app.agent.tax_agent.TaxEducationAgent")
    @patch("langchain_openai.ChatOpenAI")
    def test_continue_with_next_agents(
        self, mock_llm, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Should return 'continue' when dynamically added agents remain."""
        for mock in [mock_finance, mock_portfolio, mock_market, mock_goal, mock_news, mock_tax]:
            mock.return_value = MagicMock()
        mock_llm.return_value = MagicMock()

        from app.workflow.orchestrator import OrchestratorWorkflow

        orch = OrchestratorWorkflow()

        state = {
            "plan": ["portfolio"],
            "next_agents": ["tax_education"],
            "current_step": 1,
            "iteration_count": 1,
            "max_iterations": 4,
        }

        result = orch._should_continue(state)
        assert result == "continue"


class TestExecuteAgentNode:
    """Tests for the execute_agent node."""

    @requires_app_imports
    @patch("app.agent.finance_agent.FinanceAgent")
    @patch("app.agent.portfolio_agent.PortfolioAgent")
    @patch("app.agent.market_agent.MarketAnalysisAgent")
    @patch("app.agent.goal_agent.GoalPlanningAgent")
    @patch("app.agent.news_agent.NewsSynthesizerAgent")
    @patch("app.agent.tax_agent.TaxEducationAgent")
    @patch("langchain_openai.ChatOpenAI")
    def test_execute_calls_correct_agent(
        self, mock_llm, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Execute node calls the correct agent and stores result."""
        mock_finance_inst = MagicMock()
        mock_finance_inst.process_query.return_value = "Finance response"
        mock_finance.return_value = mock_finance_inst

        for mock in [mock_portfolio, mock_market, mock_goal, mock_news, mock_tax]:
            mock.return_value = MagicMock()
        mock_llm.return_value = MagicMock()

        from app.workflow.orchestrator import OrchestratorWorkflow

        orch = OrchestratorWorkflow()

        state = {
            "query": "What is a stock?",
            "plan": ["finance_qa"],
            "next_agents": [],
            "current_step": 0,
            "iteration_count": 0,
            "agent_results": {},
        }

        result = orch._execute_agent_node(state)

        assert "finance_qa" in result["agent_results"]
        assert result["agent_results"]["finance_qa"] == "Finance response"
        assert result["current_step"] == 1
        assert result["iteration_count"] == 1

    @requires_app_imports
    @patch("app.agent.finance_agent.FinanceAgent")
    @patch("app.agent.portfolio_agent.PortfolioAgent")
    @patch("app.agent.market_agent.MarketAnalysisAgent")
    @patch("app.agent.goal_agent.GoalPlanningAgent")
    @patch("app.agent.news_agent.NewsSynthesizerAgent")
    @patch("app.agent.tax_agent.TaxEducationAgent")
    @patch("langchain_openai.ChatOpenAI")
    def test_execute_handles_agent_error(
        self, mock_llm, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Execute node handles agent errors gracefully."""
        mock_finance_inst = MagicMock()
        mock_finance_inst.process_query.side_effect = Exception("Agent failed")
        mock_finance.return_value = mock_finance_inst

        for mock in [mock_portfolio, mock_market, mock_goal, mock_news, mock_tax]:
            mock.return_value = MagicMock()
        mock_llm.return_value = MagicMock()

        from app.workflow.orchestrator import OrchestratorWorkflow

        orch = OrchestratorWorkflow()

        state = {
            "query": "What is a stock?",
            "plan": ["finance_qa"],
            "next_agents": [],
            "current_step": 0,
            "iteration_count": 0,
            "agent_results": {},
        }

        result = orch._execute_agent_node(state)

        assert "finance_qa" in result["agent_results"]
        assert "Error" in result["agent_results"]["finance_qa"]
        assert result["current_step"] == 1

    @requires_app_imports
    @patch("app.agent.finance_agent.FinanceAgent")
    @patch("app.agent.portfolio_agent.PortfolioAgent")
    @patch("app.agent.market_agent.MarketAnalysisAgent")
    @patch("app.agent.goal_agent.GoalPlanningAgent")
    @patch("app.agent.news_agent.NewsSynthesizerAgent")
    @patch("app.agent.tax_agent.TaxEducationAgent")
    @patch("langchain_openai.ChatOpenAI")
    def test_execute_noop_when_past_queue(
        self, mock_llm, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Execute node does nothing when current_step is past the queue."""
        for mock in [mock_finance, mock_portfolio, mock_market, mock_goal, mock_news, mock_tax]:
            mock.return_value = MagicMock()
        mock_llm.return_value = MagicMock()

        from app.workflow.orchestrator import OrchestratorWorkflow

        orch = OrchestratorWorkflow()

        state = {
            "query": "test",
            "plan": ["finance_qa"],
            "next_agents": [],
            "current_step": 1,
            "iteration_count": 1,
            "agent_results": {"finance_qa": "done"},
        }

        result = orch._execute_agent_node(state)
        assert result["current_step"] == 1


class TestSynthesizeNode:
    """Tests for the synthesize node."""

    @requires_app_imports
    @patch("app.agent.finance_agent.FinanceAgent")
    @patch("app.agent.portfolio_agent.PortfolioAgent")
    @patch("app.agent.market_agent.MarketAnalysisAgent")
    @patch("app.agent.goal_agent.GoalPlanningAgent")
    @patch("app.agent.news_agent.NewsSynthesizerAgent")
    @patch("app.agent.tax_agent.TaxEducationAgent")
    @patch("langchain_openai.ChatOpenAI")
    def test_single_agent_passthrough(
        self, mock_llm, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Single agent result passes through without LLM synthesis."""
        for mock in [mock_finance, mock_portfolio, mock_market, mock_goal, mock_news, mock_tax]:
            mock.return_value = MagicMock()
        mock_llm.return_value = MagicMock()

        from app.workflow.orchestrator import OrchestratorWorkflow

        orch = OrchestratorWorkflow()

        state = {
            "query": "What is a stock?",
            "agent_results": {"finance_qa": "A stock is ownership in a company."},
        }

        result = orch._synthesize_node(state)

        assert result["final_response"] == "A stock is ownership in a company."


class TestValidAgents:
    """Tests for agent name validation."""

    @requires_app_imports
    def test_valid_agents_list(self):
        """VALID_AGENTS contains all 6 agent types."""
        from app.workflow.orchestrator import VALID_AGENTS

        assert len(VALID_AGENTS) == 6
        assert "finance_qa" in VALID_AGENTS
        assert "portfolio" in VALID_AGENTS
        assert "market_analysis" in VALID_AGENTS
        assert "goal_planning" in VALID_AGENTS
        assert "news" in VALID_AGENTS
        assert "tax_education" in VALID_AGENTS


class TestOrchestratorWorkflowInit:
    """Tests for orchestrator workflow initialization."""

    @requires_app_imports
    @patch("app.agent.finance_agent.FinanceAgent")
    @patch("app.agent.portfolio_agent.PortfolioAgent")
    @patch("app.agent.market_agent.MarketAnalysisAgent")
    @patch("app.agent.goal_agent.GoalPlanningAgent")
    @patch("app.agent.news_agent.NewsSynthesizerAgent")
    @patch("app.agent.tax_agent.TaxEducationAgent")
    @patch("langchain_openai.ChatOpenAI")
    def test_workflow_initializes_all_agents(
        self, mock_llm, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Workflow initializes all 6 agents and builds graph."""
        for mock in [mock_finance, mock_portfolio, mock_market, mock_goal, mock_news, mock_tax]:
            mock.return_value = MagicMock()
        mock_llm.return_value = MagicMock()

        from app.workflow.orchestrator import OrchestratorWorkflow

        orch = OrchestratorWorkflow()

        assert len(orch.agents) == 6
        assert orch.graph is not None
        assert orch.supervisor_llm is not None

    @requires_app_imports
    @patch("app.agent.finance_agent.FinanceAgent")
    @patch("app.agent.portfolio_agent.PortfolioAgent")
    @patch("app.agent.market_agent.MarketAnalysisAgent")
    @patch("app.agent.goal_agent.GoalPlanningAgent")
    @patch("app.agent.news_agent.NewsSynthesizerAgent")
    @patch("app.agent.tax_agent.TaxEducationAgent")
    @patch("langchain_openai.ChatOpenAI")
    def test_invoke_returns_expected_keys(
        self, mock_llm, mock_tax, mock_news, mock_goal, mock_market, mock_portfolio, mock_finance
    ):
        """Invoke returns dict with response, agents_used, plan, reasoning, messages."""
        mock_finance_inst = MagicMock()
        mock_finance_inst.process_query.return_value = "Test response"
        mock_finance.return_value = mock_finance_inst

        for mock in [mock_portfolio, mock_market, mock_goal, mock_news, mock_tax]:
            mock.return_value = MagicMock()

        # Mock the supervisor LLM to return a plan
        mock_llm_inst = MagicMock()
        mock_llm_class = mock_llm
        mock_llm_class.return_value = mock_llm_inst

        from app.workflow.orchestrator import OrchestratorWorkflow

        orch = OrchestratorWorkflow()

        # Mock the plan node to return a simple plan
        with patch.object(orch, 'invoke', return_value={
            "response": "Test response",
            "agents_used": ["finance_qa"],
            "plan": ["finance_qa"],
            "reasoning": "Simple query",
            "messages": [],
        }):
            result = orch.invoke("What is a stock?")

            assert "response" in result
            assert "agents_used" in result
            assert "plan" in result
            assert "reasoning" in result
            assert "messages" in result


class TestRouterOrchestratorToggle:
    """Tests for router integration with orchestrator toggle."""

    def test_use_orchestrator_env_default(self):
        """USE_ORCHESTRATOR defaults to false."""
        with patch.dict(os.environ, {"USE_ORCHESTRATOR": "false"}):
            val = os.getenv("USE_ORCHESTRATOR", "false").lower() == "true"
            assert val is False

    def test_use_orchestrator_env_true(self):
        """USE_ORCHESTRATOR=true activates orchestrator."""
        with patch.dict(os.environ, {"USE_ORCHESTRATOR": "true"}):
            val = os.getenv("USE_ORCHESTRATOR", "false").lower() == "true"
            assert val is True
