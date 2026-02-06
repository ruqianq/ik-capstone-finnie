"""
Agent Orchestrator for FinnIE Multi-Agent System.

Implements a supervisor pattern using LangGraph where a central LLM:
1. Plans which agents to call based on the query
2. Executes agents sequentially, collecting results
3. Reviews if more agents are needed
4. Synthesizes all results into a coherent response

Graph topology:
    plan → execute_agent → review --[continue]--> execute_agent
                              |
                              +--[synthesize]--> synthesize → END
"""

from typing import TypedDict, Literal, Annotated, List, Optional, Dict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from opentelemetry import trace
import operator
import json

from app.agent.finance_agent import FinanceAgent
from app.agent.portfolio_agent import PortfolioAgent
from app.agent.goal_agent import GoalPlanningAgent
from app.agent.market_agent import MarketAnalysisAgent
from app.agent.news_agent import NewsSynthesizerAgent
from app.agent.tax_agent import TaxEducationAgent

tracer = trace.get_tracer(__name__)

# --- Agent type definitions ---

AgentType = Literal[
    "finance_qa", "portfolio", "market_analysis",
    "goal_planning", "news", "tax_education"
]

VALID_AGENTS = [
    "finance_qa", "portfolio", "market_analysis",
    "goal_planning", "news", "tax_education"
]

# --- State schema ---


class OrchestratorState(TypedDict):
    """State for the orchestrator workflow."""
    query: str
    messages: Annotated[List[dict], operator.add]
    context: Optional[str]
    plan: List[str]
    agent_results: Dict[str, str]
    current_step: int
    iteration_count: int
    max_iterations: int
    needs_more_agents: bool
    next_agents: List[str]
    final_response: Optional[str]
    orchestrator_reasoning: str


# --- LLM Prompts ---

PLANNING_SYSTEM_PROMPT = """You are a financial advisor supervisor. Analyze the user's query and decide which specialist agents to consult, and in what order.

Available agents:
- finance_qa: General financial education (what is X, how does Y work). Uses RAG knowledge base.
- portfolio: Portfolio management, stock prices, adding/viewing holdings, specific stock queries.
- market_analysis: Market overview, sector analysis, indices (S&P, Dow, NASDAQ), technical indicators.
- goal_planning: Financial goals, saving plans, retirement planning, budgeting calculations.
- news: Financial news, market updates, recent headlines, sentiment analysis.
- tax_education: Tax questions, 401k, IRA, Roth, HSA, capital gains, tax strategies.

Rules:
1. For simple queries that clearly map to ONE agent, return just that agent.
2. For complex queries that span multiple domains, list agents in logical order (e.g., get data first, then analyze).
3. Never include more than 4 agents.
4. Consider dependencies: if the user asks about tax implications of their portfolio, call portfolio first (to get holdings), then tax_education.

Respond in JSON format ONLY:
{{"agents": ["agent_name_1", "agent_name_2"], "reasoning": "brief explanation"}}

Examples:
- "What is compound interest?" -> {{"agents": ["finance_qa"], "reasoning": "Simple education question"}}
- "How should I rebalance my portfolio given current market conditions?" -> {{"agents": ["portfolio", "market_analysis"], "reasoning": "Need portfolio data and market context to advise on rebalancing"}}
- "I want to save $50k. What are the tax-advantaged options and how is the market?" -> {{"agents": ["goal_planning", "tax_education", "market_analysis"], "reasoning": "Goal planning + tax options + market context"}}
- "Should I sell my AAPL given market conditions and tax implications?" -> {{"agents": ["portfolio", "market_analysis", "tax_education"], "reasoning": "Need current holdings, market analysis, and tax impact"}}"""

REVIEW_SYSTEM_PROMPT = """You are a financial advisor supervisor reviewing intermediate results.

You have received results from one or more agents. Decide if the user's query has been sufficiently answered, or if additional agents should be consulted.

Available agents not yet called: {remaining_agents}

Rules:
1. If the collected results fully answer the query, respond with {{"needs_more": false}}
2. If critical information is missing, add agents. But NEVER add more than 2 additional agents.
3. Do NOT re-call an agent that has already been called.
4. Prefer completing with current results over adding unnecessary agents.

Respond in JSON format ONLY:
{{"needs_more": true/false, "additional_agents": ["agent_name"], "reasoning": "why"}}"""

SYNTHESIS_SYSTEM_PROMPT = """You are a financial advisor synthesizing information from multiple specialist agents into a single, coherent response for the user.

Guidelines:
1. Combine all agent outputs into a natural, flowing response.
2. Remove redundancy - do not repeat the same information from different agents.
3. Organize the response logically (e.g., current situation -> analysis -> recommendations).
4. Preserve specific data points (prices, percentages, dates, limits) exactly as provided.
5. If agents provided conflicting information, note the discrepancy.
6. Add a brief section header for each distinct topic area using markdown.
7. Keep the response comprehensive but not excessively long.
8. End with a brief summary or actionable takeaway when appropriate."""


# --- Orchestrator Workflow ---


class OrchestratorWorkflow:
    """LangGraph workflow implementing the supervisor orchestrator pattern."""

    def __init__(self):
        self.supervisor_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.agents = {
            "finance_qa": FinanceAgent(),
            "portfolio": PortfolioAgent(),
            "market_analysis": MarketAnalysisAgent(),
            "goal_planning": GoalPlanningAgent(),
            "news": NewsSynthesizerAgent(),
            "tax_education": TaxEducationAgent(),
        }
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build the orchestrator LangGraph with plan-execute-review-synthesize cycle."""
        workflow = StateGraph(OrchestratorState)

        # Add nodes
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("execute_agent", self._execute_agent_node)
        workflow.add_node("review", self._review_node)
        workflow.add_node("synthesize", self._synthesize_node)

        # Entry point
        workflow.set_entry_point("plan")

        # Edges
        workflow.add_edge("plan", "execute_agent")
        workflow.add_edge("execute_agent", "review")

        # Conditional: review decides to continue executing or synthesize
        workflow.add_conditional_edges(
            "review",
            self._should_continue,
            {
                "continue": "execute_agent",
                "synthesize": "synthesize",
            }
        )

        workflow.add_edge("synthesize", END)

        return workflow.compile()

    # --- Node implementations ---

    def _plan_node(self, state: OrchestratorState) -> dict:
        """Supervisor LLM analyzes query and creates an execution plan."""
        with tracer.start_as_current_span("orchestrator_plan") as span:
            query = state["query"]
            context = state.get("context") or ""

            prompt = ChatPromptTemplate.from_messages([
                ("system", PLANNING_SYSTEM_PROMPT),
                ("human", "Query: {query}\nContext: {context}")
            ])
            chain = prompt | self.supervisor_llm | StrOutputParser()

            try:
                result = chain.invoke({"query": query, "context": context or "None"})
                parsed = json.loads(result)
                agents = parsed.get("agents", [])
                reasoning = parsed.get("reasoning", "")

                # Validate agent names
                valid = [a for a in agents if a in VALID_AGENTS]
                if not valid:
                    valid = ["finance_qa"]

                span.set_attribute("orchestrator.plan", json.dumps(valid))
                span.set_attribute("orchestrator.reasoning", reasoning)

                return {
                    "plan": valid,
                    "agent_results": {},
                    "current_step": 0,
                    "iteration_count": 0,
                    "max_iterations": min(len(valid) + 2, 4),
                    "needs_more_agents": False,
                    "next_agents": [],
                    "orchestrator_reasoning": reasoning,
                    "messages": [{"role": "system", "content": f"Plan: {valid} ({reasoning})"}],
                }
            except Exception as e:
                span.set_attribute("orchestrator.plan_error", str(e))
                return {
                    "plan": ["finance_qa"],
                    "agent_results": {},
                    "current_step": 0,
                    "iteration_count": 0,
                    "max_iterations": 4,
                    "needs_more_agents": False,
                    "next_agents": [],
                    "orchestrator_reasoning": f"Planning failed ({e}), defaulting to finance_qa",
                    "messages": [],
                }

    def _execute_agent_node(self, state: OrchestratorState) -> dict:
        """Execute the next agent in the plan."""
        execution_queue = state["plan"] + state["next_agents"]
        step = state["current_step"]

        if step >= len(execution_queue):
            return {"current_step": step, "iteration_count": state["iteration_count"]}

        agent_name = execution_queue[step]

        with tracer.start_as_current_span(f"orchestrator_execute_{agent_name}") as span:
            span.set_attribute("orchestrator.agent", agent_name)
            span.set_attribute("orchestrator.step", step)

            try:
                agent = self.agents[agent_name]
                response = agent.process_query(state["query"])
                span.set_attribute("orchestrator.agent_response_length", len(response))
            except Exception as e:
                response = f"Error from {agent_name}: {str(e)}"
                span.set_attribute("orchestrator.agent_error", str(e))

            # Build updated results dict
            updated_results = dict(state["agent_results"])
            updated_results[agent_name] = response

            return {
                "agent_results": updated_results,
                "current_step": step + 1,
                "iteration_count": state["iteration_count"] + 1,
                "messages": [{"role": "assistant", "content": response, "agent": agent_name}],
            }

    def _review_node(self, state: OrchestratorState) -> dict:
        """Review results and decide if more agents are needed."""
        execution_queue = state["plan"] + state["next_agents"]
        step = state["current_step"]
        iteration_count = state["iteration_count"]

        with tracer.start_as_current_span("orchestrator_review") as span:
            # Hit max iterations — force synthesize
            if iteration_count >= state["max_iterations"]:
                span.set_attribute("orchestrator.review_decision", "synthesize_max_iterations")
                return {"needs_more_agents": False}

            # Still have planned agents to execute — continue without LLM call
            if step < len(execution_queue):
                span.set_attribute("orchestrator.review_decision", "continue_planned")
                return {"needs_more_agents": True}

            # All planned agents done — ask LLM if more agents would help
            called_agents = set(state["agent_results"].keys())
            remaining = [a for a in VALID_AGENTS if a not in called_agents]

            if not remaining:
                span.set_attribute("orchestrator.review_decision", "synthesize_all_called")
                return {"needs_more_agents": False}

            # LLM review
            results_summary = "\n\n".join([
                f"--- {name} ---\n{text[:500]}"
                for name, text in state["agent_results"].items()
            ])

            prompt = ChatPromptTemplate.from_messages([
                ("system", REVIEW_SYSTEM_PROMPT),
                ("human", "Original query: {query}\n\nResults collected so far:\n{results}")
            ])
            chain = prompt | self.supervisor_llm | StrOutputParser()

            try:
                result = chain.invoke({
                    "query": state["query"],
                    "results": results_summary,
                    "remaining_agents": ", ".join(remaining),
                })
                parsed = json.loads(result)
                needs_more = parsed.get("needs_more", False)
                additional = parsed.get("additional_agents", [])

                # Validate and cap at 2 additions
                additional = [a for a in additional if a in remaining][:2]

                span.set_attribute("orchestrator.review_needs_more", needs_more)
                span.set_attribute("orchestrator.review_additional", json.dumps(additional))

                if needs_more and additional:
                    return {
                        "needs_more_agents": True,
                        "next_agents": state["next_agents"] + additional,
                    }
                return {"needs_more_agents": False}

            except Exception as e:
                span.set_attribute("orchestrator.review_error", str(e))
                return {"needs_more_agents": False}

    def _should_continue(self, state: OrchestratorState) -> str:
        """Routing function: continue executing agents or synthesize."""
        execution_queue = state["plan"] + state["next_agents"]
        step = state["current_step"]

        if step < len(execution_queue) and state["iteration_count"] < state["max_iterations"]:
            return "continue"
        return "synthesize"

    def _synthesize_node(self, state: OrchestratorState) -> dict:
        """Combine all agent results into a final coherent response."""
        with tracer.start_as_current_span("orchestrator_synthesize") as span:
            agent_results = state["agent_results"]

            # Single agent — pass through directly (no synthesis overhead)
            if len(agent_results) == 1:
                sole_response = list(agent_results.values())[0]
                span.set_attribute("orchestrator.synthesis_mode", "passthrough")
                span.set_attribute("orchestrator.agents_used", json.dumps(list(agent_results.keys())))
                return {"final_response": sole_response}

            # Multiple agents — synthesize via LLM
            results_text = "\n\n".join([
                f"=== {name.replace('_', ' ').title()} Agent ===\n{text}"
                for name, text in agent_results.items()
            ])

            prompt = ChatPromptTemplate.from_messages([
                ("system", SYNTHESIS_SYSTEM_PROMPT),
                ("human", "User query: {query}\n\nAgent outputs:\n{results}\n\nSynthesize into a single coherent response:")
            ])
            chain = prompt | self.supervisor_llm | StrOutputParser()

            try:
                response = chain.invoke({
                    "query": state["query"],
                    "results": results_text,
                })
                span.set_attribute("orchestrator.synthesis_mode", "llm")
                span.set_attribute("orchestrator.agents_used", json.dumps(list(agent_results.keys())))
                return {"final_response": response}
            except Exception as e:
                # Fallback: concatenate with headers
                span.set_attribute("orchestrator.synthesis_error", str(e))
                fallback = "\n\n---\n\n".join([
                    f"**{name.replace('_', ' ').title()}**:\n{text}"
                    for name, text in agent_results.items()
                ])
                return {"final_response": fallback}

    # --- Public interface ---

    def invoke(self, query: str, context: str = None, messages: List[dict] = None) -> dict:
        """
        Invoke the orchestrator workflow.

        Args:
            query: The user's query
            context: Optional conversation context
            messages: Optional message history

        Returns:
            dict with 'response', 'agents_used', 'plan', 'reasoning', 'messages'
        """
        initial_state = {
            "query": query,
            "messages": messages or [{"role": "user", "content": query}],
            "context": context,
            "plan": [],
            "agent_results": {},
            "current_step": 0,
            "max_iterations": 4,
            "iteration_count": 0,
            "needs_more_agents": False,
            "next_agents": [],
            "final_response": None,
            "orchestrator_reasoning": "",
        }

        result = self.graph.invoke(initial_state)

        return {
            "response": result.get("final_response", "I could not process your request."),
            "agents_used": list(result.get("agent_results", {}).keys()),
            "plan": result.get("plan", []),
            "reasoning": result.get("orchestrator_reasoning", ""),
            "messages": result.get("messages", []),
        }


# --- Module-level lazy initialization ---

_orchestrator_instance = None


def get_orchestrator() -> OrchestratorWorkflow:
    """Get or create the global orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorWorkflow()
    return _orchestrator_instance
