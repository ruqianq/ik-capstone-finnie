"""
FinnIE - Multi-Agent Personal Financial Advisor
Enhanced Streamlit UI
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.observability import setup_observability
from app.agent.router import route_and_process

# Initialize Tracing
tracer = setup_observability()

# Page Configuration
st.set_page_config(
    page_title="FinnIE - Financial Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        background: linear-gradient(90deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        color: white;
    }

    /* Agent badge styling */
    .agent-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 0.5rem;
    }

    .agent-finance { background-color: #4CAF50; color: white; }
    .agent-portfolio { background-color: #2196F3; color: white; }
    .agent-market { background-color: #FF9800; color: white; }
    .agent-goal { background-color: #9C27B0; color: white; }
    .agent-news { background-color: #00BCD4; color: white; }
    .agent-tax { background-color: #F44336; color: white; }

    /* Quick action button styling */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid #ddd;
        padding: 0.5rem;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        border-color: #1e3a5f;
        background-color: #f0f7ff;
    }

    /* Sidebar styling */
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    /* Chat message styling */
    .stChatMessage {
        border-radius: 10px;
    }

    /* Info box styling */
    .info-box {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "show_welcome" not in st.session_state:
        st.session_state.show_welcome = True


def render_sidebar():
    """Render the sidebar with agent info and quick actions."""
    with st.sidebar:
        # Logo and title
        st.markdown("## 💰 FinnIE")
        st.markdown("*Your AI Financial Advisor*")
        st.divider()

        # Agent Status Section
        st.markdown("### 🤖 Available Agents")

        agents = [
            ("📚 Finance Q&A", "General financial education", "finance"),
            ("📊 Portfolio", "Track holdings & prices", "portfolio"),
            ("📈 Market Analysis", "Market trends & sectors", "market"),
            ("🎯 Goal Planning", "Savings & retirement", "goal"),
            ("📰 News", "Market news & updates", "news"),
            ("💵 Tax Education", "Tax strategies & accounts", "tax"),
        ]

        for name, desc, _ in agents:
            with st.expander(name):
                st.caption(desc)

        st.divider()

        # Quick Actions Section
        st.markdown("### ⚡ Quick Actions")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📊 Portfolio", use_container_width=True):
                st.session_state.quick_action = "Show my portfolio"
                st.rerun()

        with col2:
            if st.button("📈 Market", use_container_width=True):
                st.session_state.quick_action = "How is the market today?"
                st.rerun()

        col3, col4 = st.columns(2)

        with col3:
            if st.button("📰 News", use_container_width=True):
                st.session_state.quick_action = "What's the latest market news?"
                st.rerun()

        with col4:
            if st.button("💵 Tax Tips", use_container_width=True):
                st.session_state.quick_action = "What are the 401k contribution limits?"
                st.rerun()

        st.divider()

        # Settings Section
        st.markdown("### ⚙️ Settings")

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.show_welcome = True
            st.rerun()

        # Export chat
        if st.session_state.messages:
            chat_export = "\n\n".join([
                f"{'User' if m['role'] == 'user' else 'FinnIE'}: {m['content']}"
                for m in st.session_state.messages
            ])
            st.download_button(
                "📥 Export Chat",
                chat_export,
                file_name=f"finnie_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

        st.divider()

        # Footer
        st.caption("Powered by LangGraph + OpenAI")
        st.caption(f"Session: {datetime.now().strftime('%Y-%m-%d')}")


def render_welcome_message():
    """Render the welcome message with example queries."""
    st.markdown("""
    <div class="main-header">
        <h1 style="margin:0; color:white;">👋 Welcome to FinnIE!</h1>
        <p style="margin:0.5rem 0 0 0; opacity:0.9;">Your intelligent multi-agent financial advisor</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Try asking me about:")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📚 Learn")
        examples = [
            "What is compound interest?",
            "Explain ETFs vs mutual funds",
            "How does diversification work?",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.quick_action = ex
                st.session_state.show_welcome = False
                st.rerun()

    with col2:
        st.markdown("#### 💼 Invest")
        examples = [
            "Price of AAPL",
            "Add 10 shares of MSFT",
            "Show sector performance",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.quick_action = ex
                st.session_state.show_welcome = False
                st.rerun()

    with col3:
        st.markdown("#### 🎯 Plan")
        examples = [
            "Save $50,000 in 5 years",
            "Retirement planning tips",
            "What is a Roth IRA?",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.quick_action = ex
                st.session_state.show_welcome = False
                st.rerun()

    st.markdown("---")

    # Info boxes
    col1, col2 = st.columns(2)

    with col1:
        st.info("💡 **Tip:** I can track your portfolio! Try 'Add 10 shares of AAPL' to get started.")

    with col2:
        st.info("📊 **Tip:** Ask about market trends with 'How is the S&P 500 doing?' or 'Show sector performance'.")


def get_agent_badge(response: str) -> str:
    """Determine which agent handled the response and return a badge."""
    response_lower = response.lower()

    # Check for agent indicators in response
    if "knowledge base" in response_lower or "source: internal" in response_lower:
        return '<span class="agent-badge agent-finance">📚 Finance Q&A</span>'
    elif "portfolio" in response_lower and ("added" in response_lower or "shares" in response_lower):
        return '<span class="agent-badge agent-portfolio">📊 Portfolio</span>'
    elif any(x in response_lower for x in ["s&p", "dow", "nasdaq", "sector", "market overview"]):
        return '<span class="agent-badge agent-market">📈 Market</span>'
    elif any(x in response_lower for x in ["save", "goal", "retirement", "monthly"]):
        return '<span class="agent-badge agent-goal">🎯 Goal Planning</span>'
    elif "news" in response_lower or "headline" in response_lower:
        return '<span class="agent-badge agent-news">📰 News</span>'
    elif any(x in response_lower for x in ["tax", "401k", "ira", "roth", "deduction"]):
        return '<span class="agent-badge agent-tax">💵 Tax</span>'

    return '<span class="agent-badge agent-finance">📚 Finance Q&A</span>'


def render_chat():
    """Render the chat interface."""
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and "badge" in message:
                st.markdown(message["badge"], unsafe_allow_html=True)
            st.markdown(message["content"])

    # Handle quick action from sidebar or welcome
    if "quick_action" in st.session_state and st.session_state.quick_action:
        prompt = st.session_state.quick_action
        st.session_state.quick_action = None
        process_message(prompt)

    # Chat input
    if prompt := st.chat_input("Ask me anything about finance, investing, or your portfolio..."):
        st.session_state.show_welcome = False
        process_message(prompt)


def process_message(prompt: str):
    """Process a user message and generate response."""
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Process with Agent Router
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            with tracer.start_as_current_span("streamlit_interaction") as span:
                span.set_attribute("openinference.span.kind", "CHAIN")
                span.set_attribute("input.value", prompt)

                try:
                    response = route_and_process(prompt)
                    span.set_attribute("output.value", response)
                except Exception as e:
                    response = f"I encountered an error processing your request. Please try again. Error: {str(e)}"
                    span.set_attribute("error", str(e))

        # Get agent badge
        badge = get_agent_badge(response)
        st.markdown(badge, unsafe_allow_html=True)
        st.markdown(response)

    # Add assistant response to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "badge": badge
    })

    st.rerun()


def main():
    """Main application entry point."""
    init_session_state()
    render_sidebar()

    # Main content area
    if st.session_state.show_welcome and not st.session_state.messages:
        render_welcome_message()

    render_chat()


if __name__ == "__main__":
    main()
