import streamlit as st
import pandas as pd
import plotly.express as px
from database import create_connection, create_tables

create_tables()

st.set_page_config(page_title="Energy", page_icon="⚡", layout="wide")
st.title("⚡ Energy Tracker")
st.divider()

#Add new reading
st.subheader("Add New Reading")

col1, col2, col3, col4 = st.columns(4)

with col1:
    date = st.date_input("Date")
with col2:
    gas_reading = st.number_input("Gas Reading (m³)", min_value=0.0, step=0.1)
with col3:
    electricity_reading = st.number_input("Electricity Reading (kWh)", min_value=0.0, step=0.1)
with col4:
    electricity_kwh = st.number_input("Power Used This Month (kWh)", min_value=0.0, step=0.1)

notes = st.text_input("Notes (optional)")

if st.button("💾 Save Reading"):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO energy (date, gas_reading, electricity_reading, electricity_kwh, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (str(date), gas_reading, electricity_reading, electricity_kwh, notes))
    conn.commit()
    conn.close()
    st.success("Reading saved!")
    st.rerun()

st.divider()

#Load data
conn = create_connection()
energy_df = pd.read_sql_query("SELECT * FROM energy ORDER BY date", conn)
conn.close()

if energy_df.empty:
    st.warning("No energy data yet. Add your first reading above.")
else:
    #Metrics
    st.subheader("📊 Overview")
    col1, col2, col3 = st.columns(3)

    with col1:
        latest_gas = energy_df["gas_reading"].iloc[-1]
        st.metric("Latest Gas Reading", f"{latest_gas} m³")

    with col2:
        latest_elec = energy_df["electricity_reading"].iloc[-1]
        st.metric("Latest Electricity Reading", f"{latest_elec} kWh")

    with col3:
        total_kwh = energy_df["electricity_kwh"].sum()
        st.metric("Total Power Used", f"{total_kwh} kWh")

    st.divider()

    #Charts
    st.subheader("📈 Charts")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(energy_df, x="date", y="gas_reading",
                      title="Gas Readings Over Time (m³)",
                      markers=True,
                      color_discrete_sequence=["#FF6B35"])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(energy_df, x="date", y="electricity_reading",
                      title="Electricity Meter Readings (kWh)",
                      markers=True,
                      color_discrete_sequence=["#FFD700"])
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(energy_df, x="date", y="electricity_kwh",
                     title="Monthly Power Consumption (kWh)",
                     color_discrete_sequence=["#00CC96"])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.area(energy_df, x="date", y="gas_reading",
                      title="Gas Usage Area Chart",
                      color_discrete_sequence=["#FF6B35"])
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    #Raw data
    st.subheader("📋 Raw Data")
    st.dataframe(energy_df, use_container_width=True)
