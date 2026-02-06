"""
LangGraph Workflow Orchestration for FinnIE Multi-Agent System.

This module implements a StateGraph that routes user queries to specialized
financial agents using LLM-based intent classification.

Flow:
User Query -> Intent Classifier -> Appropriate Agent -> Response
"""

from typing import TypedDict, Literal, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import operator
import os

# Import agents
from app.agent.finance_agent import FinanceAgent
from app.agent.portfolio_agent import PortfolioAgent
from app.agent.goal_agent import GoalPlanningAgent
from app.agent.market_agent import MarketAnalysisAgent
from app.agent.news_agent import NewsSynthesizerAgent
from app.agent.tax_agent import TaxEducationAgent


# Define the possible intents/agents
AgentType = Literal[
    "finance_qa",
    "portfolio",
    "market_analysis",
    "goal_planning",
    "news",
    "tax_education"
]


class ConversationState(TypedDict):
    """State schema for the conversation workflow."""
    # Current user query
    query: str
    # Conversation history (list of messages)
    messages: Annotated[List[dict], operator.add]
    # Classified intent
    intent: Optional[AgentType]
    # Agent response
    response: Optional[str]
    # Context from previous turns (for multi-turn conversations)
    context: Optional[str]


class IntentClassifier:
    """LLM-based intent classifier for routing queries to appropriate agents."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intent classifier for a financial assistant.
Classify the user's query into ONE of these categories:

- finance_qa: General financial education questions (what is X, how does Y work, explain Z)
- portfolio: Portfolio management, stock prices, adding/viewing holdings, specific stock queries
- market_analysis: Market overview, sector analysis, trends, technical analysis, indices (S&P, Dow, NASDAQ)
- goal_planning: Financial goals, saving plans, retirement planning, budgeting
- news: Financial news, market updates, what's happening in the market
- tax_education: Tax questions, 401k, IRA, Roth, HSA, capital gains, tax strategies

Respond with ONLY the category name, nothing else.

Examples:
- "What is compound interest?" -> finance_qa
- "Price of AAPL" -> portfolio
- "How is the market today?" -> market_analysis
- "I want to save $50,000 for a house" -> goal_planning
- "Latest news on Tesla" -> news
- "What is a Roth IRA?" -> tax_education
- "Add 10 shares of MSFT" -> portfolio
- "Show me sector performance" -> market_analysis"""),
            ("human", "{query}")
        ])

    def classify(self, query: str) -> AgentType:
        """Classify the query intent."""
        chain = self.prompt | self.llm | StrOutputParser()
        try:
            result = chain.invoke({"query": query}).strip().lower()
            # Validate the result
            valid_intents = [
                "finance_qa", "portfolio", "market_analysis",
                "goal_planning", "news", "tax_education"
            ]
            if result in valid_intents:
                return result
            # Default to finance_qa if unrecognized
            return "finance_qa"
        except Exception as e:
            print(f"Intent classification error: {e}")
            return "finance_qa"


class FinancialWorkflow:
    """LangGraph workflow for multi-agent financial assistant."""

    def __init__(self):
        # Initialize classifier
        self.classifier = IntentClassifier()

        # Initialize all agents
        self.agents = {
            "finance_qa": FinanceAgent(),
            "portfolio": PortfolioAgent(),
            "market_analysis": MarketAnalysisAgent(),
            "goal_planning": GoalPlanningAgent(),
            "news": NewsSynthesizerAgent(),
            "tax_education": TaxEducationAgent()
        }

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create the graph with our state schema
        workflow = StateGraph(ConversationState)

        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent_node)
        workflow.add_node("finance_qa", self._finance_qa_node)
        workflow.add_node("portfolio", self._portfolio_node)
        workflow.add_node("market_analysis", self._market_analysis_node)
        workflow.add_node("goal_planning", self._goal_planning_node)
        workflow.add_node("news", self._news_node)
        workflow.add_node("tax_education", self._tax_education_node)

        # Set entry point
        workflow.set_entry_point("classify_intent")

        # Add conditional edges from classifier to agents
        workflow.add_conditional_edges(
            "classify_intent",
            self._route_to_agent,
            {
                "finance_qa": "finance_qa",
                "portfolio": "portfolio",
                "market_analysis": "market_analysis",
                "goal_planning": "goal_planning",
                "news": "news",
                "tax_education": "tax_education"
            }
        )

        # All agents go to END
        workflow.add_edge("finance_qa", END)
        workflow.add_edge("portfolio", END)
        workflow.add_edge("market_analysis", END)
        workflow.add_edge("goal_planning", END)
        workflow.add_edge("news", END)
        workflow.add_edge("tax_education", END)

        return workflow.compile()

    def _classify_intent_node(self, state: ConversationState) -> dict:
        """Node that classifies the user's intent."""
        query = state["query"]
        # Include context for better classification in multi-turn conversations
        context = state.get("context", "")
        if context:
            full_query = f"Context: {context}\nCurrent query: {query}"
        else:
            full_query = query

        intent = self.classifier.classify(full_query)
        return {"intent": intent}

    def _route_to_agent(self, state: ConversationState) -> str:
        """Route to the appropriate agent based on classified intent."""
        return state["intent"]

    def _finance_qa_node(self, state: ConversationState) -> dict:
        """Process query with Finance Q&A agent (RAG-based)."""
        response = self.agents["finance_qa"].process_query(state["query"])
        return {
            "response": response,
            "messages": [{"role": "assistant", "content": response, "agent": "finance_qa"}]
        }

    def _portfolio_node(self, state: ConversationState) -> dict:
        """Process query with Portfolio agent."""
        response = self.agents["portfolio"].process_query(state["query"])
        return {
            "response": response,
            "messages": [{"role": "assistant", "content": response, "agent": "portfolio"}]
        }

    def _market_analysis_node(self, state: ConversationState) -> dict:
        """Process query with Market Analysis agent."""
        response = self.agents["market_analysis"].process_query(state["query"])
        return {
            "response": response,
            "messages": [{"role": "assistant", "content": response, "agent": "market_analysis"}]
        }

    def _goal_planning_node(self, state: ConversationState) -> dict:
        """Process query with Goal Planning agent."""
        response = self.agents["goal_planning"].process_query(state["query"])
        return {
            "response": response,
            "messages": [{"role": "assistant", "content": response, "agent": "goal_planning"}]
        }

    def _news_node(self, state: ConversationState) -> dict:
        """Process query with News Synthesizer agent."""
        response = self.agents["news"].process_query(state["query"])
        return {
            "response": response,
            "messages": [{"role": "assistant", "content": response, "agent": "news"}]
        }

    def _tax_education_node(self, state: ConversationState) -> dict:
        """Process query with Tax Education agent."""
        response = self.agents["tax_education"].process_query(state["query"])
        return {
            "response": response,
            "messages": [{"role": "assistant", "content": response, "agent": "tax_education"}]
        }

    def invoke(self, query: str, context: str = None, messages: List[dict] = None) -> dict:
        """
        Invoke the workflow with a user query.

        Args:
            query: The user's query
            context: Optional context from previous conversation
            messages: Optional message history

        Returns:
            dict with 'response', 'intent', and updated 'messages'
        """
        initial_state = {
            "query": query,
            "messages": messages or [{"role": "user", "content": query}],
            "intent": None,
            "response": None,
            "context": context
        }

        result = self.graph.invoke(initial_state)
        return result


# Global workflow instance (lazy initialization)
_workflow_instance = None


def get_workflow() -> FinancialWorkflow:
    """Get or create the global workflow instance."""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = FinancialWorkflow()
    return _workflow_instance


def process_with_langgraph(query: str, context: str = None) -> str:
    """
    Process a query using the LangGraph workflow.

    This is the main entry point for the router.
    """
    workflow = get_workflow()
    result = workflow.invoke(query, context=context)
    return result.get("response", "I'm sorry, I couldn't process your request.")
