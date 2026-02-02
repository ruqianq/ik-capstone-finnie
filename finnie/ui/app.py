"""Main Streamlit application for FinnIE."""

import asyncio
import streamlit as st
from datetime import datetime

from finnie.agents import router
from finnie.observability import observability, get_trace_id
from finnie.config import config


# Initialize observability
observability.initialize()

# Page configuration
st.set_page_config(
    page_title="FinnIE - Personal Financial Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .trace-id {
        font-size: 0.8rem;
        color: #666;
        font-family: monospace;
    }
    .agent-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .citation {
        font-size: 0.85rem;
        color: #555;
        font-style: italic;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "trace_ids" not in st.session_state:
        st.session_state.trace_ids = []


def display_message(role: str, content: str, trace_id: str = None, agent_type: str = None, citations: list = None):
    """Display a chat message with metadata."""
    with st.chat_message(role):
        if agent_type:
            agent_colors = {
                "finance_qa": "#4CAF50",
                "portfolio_analysis": "#2196F3",
                "market_analysis": "#FF9800",
                "goal_planning": "#9C27B0",
            }
            color = agent_colors.get(agent_type, "#666")
            st.markdown(
                f'<div class="agent-badge" style="background-color: {color}; color: white;">'
                f'Agent: {agent_type.replace("_", " ").title()}</div>',
                unsafe_allow_html=True
            )
        
        st.markdown(content)
        
        if citations:
            st.markdown("**Sources:**")
            for citation in citations:
                st.markdown(f'<div class="citation">{citation}</div>', unsafe_allow_html=True)
        
        if trace_id:
            st.markdown(f'<div class="trace-id">Trace ID: {trace_id}</div>', unsafe_allow_html=True)


async def process_query(query: str, context: dict = None):
    """Process user query through the router."""
    trace_id = get_trace_id()
    
    try:
        response = await router.process_request(
            query=query,
            context=context or {},
            trace_id=trace_id
        )
        return response
    except Exception as e:
        st.error(f"Error processing query: {e}")
        return None


def chat_tab():
    """Chat interface tab."""
    st.markdown('<div class="main-header">💬 Chat with FinnIE</div>', unsafe_allow_html=True)
    st.markdown("Ask me anything about finance, investments, portfolio analysis, or financial planning!")
    
    # Display chat history
    for msg_data in st.session_state.messages:
        display_message(
            role=msg_data["role"],
            content=msg_data["content"],
            trace_id=msg_data.get("trace_id"),
            agent_type=msg_data.get("agent_type"),
            citations=msg_data.get("citations"),
        )
    
    # Chat input
    if prompt := st.chat_input("Ask your financial question..."):
        # Display user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
        })
        display_message("user", prompt)
        
        # Process query
        with st.spinner("Thinking..."):
            response = asyncio.run(process_query(prompt))
        
        if response:
            # Display assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.response,
                "trace_id": response.trace_id,
                "agent_type": response.agent_type.value,
                "citations": response.citations,
            })
            display_message(
                "assistant",
                response.response,
                trace_id=response.trace_id,
                agent_type=response.agent_type.value,
                citations=response.citations,
            )
            st.session_state.trace_ids.append(response.trace_id)


def portfolio_tab():
    """Portfolio analysis tab."""
    st.markdown('<div class="main-header">📊 Portfolio Analysis</div>', unsafe_allow_html=True)
    
    st.markdown("### Your Portfolio")
    st.info("Portfolio analysis features coming soon! Ask about portfolio analysis in the Chat tab.")
    
    # Example portfolio input
    with st.expander("Add Holdings"):
        col1, col2, col3 = st.columns(3)
        with col1:
            ticker = st.text_input("Ticker Symbol", placeholder="AAPL")
        with col2:
            shares = st.number_input("Shares", min_value=0.0, value=0.0)
        with col3:
            price = st.number_input("Avg. Price", min_value=0.0, value=0.0)
        
        if st.button("Add to Portfolio"):
            st.success(f"Added {shares} shares of {ticker}")


def market_tab():
    """Market analysis tab."""
    st.markdown('<div class="main-header">📈 Market Analysis</div>', unsafe_allow_html=True)
    
    st.markdown("### Market Overview")
    st.info("Real-time market data coming soon! Ask about market trends in the Chat tab.")
    
    # Example market widget
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("S&P 500", "4,500", "+1.2%")
    with col2:
        st.metric("NASDAQ", "14,000", "+0.8%")
    with col3:
        st.metric("DOW", "35,000", "+0.5%")


def goals_tab():
    """Financial goals tab."""
    st.markdown('<div class="main-header">🎯 Financial Goals</div>', unsafe_allow_html=True)
    
    st.markdown("### Your Financial Goals")
    st.info("Goal tracking features coming soon! Ask about financial planning in the Chat tab.")
    
    # Example goal templates
    goal_templates = [
        "🏠 Save for a house down payment",
        "🎓 Save for college education",
        "🏖️ Plan for retirement",
        "🚗 Save for a car purchase",
    ]
    
    for template in goal_templates:
        with st.expander(template):
            st.write("Set your target amount, timeline, and track progress.")
            if st.button(f"Learn More", key=template):
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"Help me with {template.split(' ', 1)[1]}",
                })
                st.experimental_rerun()


def sidebar():
    """Sidebar with app information."""
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150.png?text=FinnIE", width=150)
        st.markdown("### FinnIE")
        st.markdown("*Multi-Agent Personal Financial Advisor*")
        st.markdown("---")
        
        st.markdown("#### About")
        st.markdown(f"**Version:** {config.app_version}")
        st.markdown(f"**Status:** 🟢 Online")
        
        st.markdown("---")
        st.markdown("#### Available Agents")
        agents = router.get_available_agents()
        for agent in agents:
            st.markdown(f"• {agent.replace('_', ' ').title()}")
        
        st.markdown("---")
        st.markdown("#### Quick Actions")
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.session_state.trace_ids = []
            st.experimental_rerun()
        
        if st.button("View Trace History"):
            if st.session_state.trace_ids:
                st.markdown("**Recent Trace IDs:**")
                for tid in st.session_state.trace_ids[-5:]:
                    st.code(tid, language="text")
            else:
                st.info("No traces yet")


def main():
    """Main application entry point."""
    initialize_session_state()
    
    # Sidebar
    sidebar()
    
    # Main content with tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📊 Portfolio", "📈 Market", "🎯 Goals"])
    
    with tab1:
        chat_tab()
    
    with tab2:
        portfolio_tab()
    
    with tab3:
        market_tab()
    
    with tab4:
        goals_tab()


if __name__ == "__main__":
    main()
