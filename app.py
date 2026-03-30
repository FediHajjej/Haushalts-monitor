
import streamlit as st
import pandas as pd
import plotly.express as px
from database import create_connection

# Page config
st.set_page_config(
    page_title="HaushaltsMonitor",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 HaushaltsMonitor")
st.markdown("Your personal home dashboard")

# ─── Load data ───────────────────────────────────────────
conn = create_connection()

energy_df = pd.read_sql_query("SELECT * FROM energy ORDER BY date", conn)
expenses_df = pd.read_sql_query("SELECT * FROM expenses ORDER BY date", conn)
speed_df = pd.read_sql_query("SELECT * FROM internet_speed ORDER BY date", conn)

conn.close()

# ─── Top metrics ─────────────────────────────────────────
st.subheader("📊 Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_expenses = expenses_df["amount"].sum()
    st.metric("Total Expenses", f"€{total_expenses:.2f}")

with col2:
    latest_gas = energy_df["gas_reading"].iloc[-1] if not energy_df.empty else 0
    st.metric("Latest Gas Reading", f"{latest_gas} m³")

with col3:
    avg_ping = speed_df["ping"].mean() if not speed_df.empty else 0
    st.metric("Average Ping", f"{avg_ping:.1f} ms")

with col4:
    avg_download = speed_df["download"].mean() if not speed_df.empty else 0
    st.metric("Average Download", f"{avg_download:.1f} Mbps")

st.divider()

# ─── Energy chart ─────────────────────────────────────────
st.subheader("⚡ Energy Readings Over Time")
col1, col2 = st.columns(2)

with col1:
    if not energy_df.empty:
        fig = px.line(energy_df, x="date", y="gas_reading",
                      title="Gas Readings (m³)",
                      markers=True,
                      color_discrete_sequence=["#FF6B35"])
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if not energy_df.empty:
        fig = px.line(energy_df, x="date", y="electricity_reading",
                      title="Electricity Readings (kWh)",
                      markers=True,
                      color_discrete_sequence=["#FFD700"])
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# ─── Expenses chart ───────────────────────────────────────
st.subheader("💶 Expenses Breakdown")
col1, col2 = st.columns(2)

with col1:
    if not expenses_df.empty:
        fig = px.pie(expenses_df, values="amount", names="category",
                     title="Expenses by Category",
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if not expenses_df.empty:
        fig = px.bar(expenses_df, x="category", y="amount",
                     title="Expenses by Category (Bar)",
                     color="category",
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# ─── Internet speed chart ─────────────────────────────────
st.subheader("🌐 Internet Speed & Ping")
col1, col2 = st.columns(2)

with col1:
    if not speed_df.empty:
        fig = px.line(speed_df, x="date", y=["download", "upload"],
                      title="Download & Upload Speed (Mbps)",
                      markers=True,
                      color_discrete_sequence=["#00CC96", "#AB63FA"])
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if not speed_df.empty:
        fig = px.line(speed_df, x="date", y="ping",
                      title="Ping Over Time (ms)",
                      markers=True,
                      color_discrete_sequence=["#EF553B"])
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# ─── Raw data tables ──────────────────────────────────────
st.subheader("📋 Raw Data")
tab1, tab2, tab3 = st.tabs(["Energy", "Expenses", "Internet Speed"])

with tab1:
    st.dataframe(energy_df, use_container_width=True)

with tab2:
    st.dataframe(expenses_df, use_container_width=True)

with tab3:
    st.dataframe(speed_df, use_container_width=True)