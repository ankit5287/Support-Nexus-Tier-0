import streamlit as st

st.set_page_config(
    page_title="DevSupport Nexus",
    page_icon="🧊",
    layout="wide",
)

st.title("Welcome to DevSupport Nexus 🧊")
st.markdown("""
### The AI-Powered Developer & Support Ecosystem.

This platform bridges the gap between your customers and your engineering team using cutting-edge Machine Learning.

**Please select a portal from the sidebar to the left:**
1. **Customer Portal:** Submit tickets, get instant search rankings, and real-time moderation.
2. **Developer Dashboard:** Review bug tickets and use the LLM Code Reviewer to fix them.
""")

st.info("👈 Use the sidebar to navigate.")
