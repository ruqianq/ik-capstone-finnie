import streamlit as st
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.observability import setup_observability
from app.agent.router import route_and_process

# Initialize Tracing
tracer = setup_observability()

st.set_page_config(page_title="FinnIE - Financial Advisor", layout="wide")

st.title("FinnIE 🤖💰")
st.markdown("Your Multi-Agent Personal Financial Advisor")

# Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask me about your portfolio or the market..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process with Agent Router
    with st.spinner("Thinking..."):
        with tracer.start_as_current_span("streamlit_interaction") as span:
            span.set_attribute("openinference.span.kind", "CHAIN")
            span.set_attribute("input.value", prompt)
            response = route_and_process(prompt)
            span.set_attribute("output.value", response)

    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
