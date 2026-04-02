import streamlit as st

st.set_page_config(
    page_title="HaushaltsMonitor",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 HaushaltsMonitor")
st.markdown("### Welcome to your personal home dashboard")
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.info("⚡ **Energy**\nTrack gas and electricity usage")

with col2:
    st.info("💶 **Expenses**\nMonitor bills and paid expenses")

with col3:
    st.info("🌐 **Internet**\nLive speed and ping tracking")

col1, col2 = st.columns(2)

with col1:
    st.info("📄 **Contracts**\nUpload and preview your contracts")

with col2:
    st.info("✏️ **Edit**\nModify any existing entry")

st.divider()
st.caption("HaushaltsMonitor — Built with Python & Streamlit")
