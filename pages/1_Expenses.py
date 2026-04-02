import streamlit as st
import pandas as pd
import plotly.express as px
from database import create_connection, create_tables

create_tables()

st.set_page_config(page_title="Expenses", page_icon="💶", layout="wide")
st.title("💶 Expenses Tracker")
st.divider()

CATEGORIES = ["Miete", "Strom", "Gas", "Internet", "Versicherung", "Transport", "Sonstiges"]

#Add new expense
st.subheader("Add New Expense")

col1, col2, col3, col4 = st.columns(4)

with col1:
    date = st.date_input("Date")
with col2:
    category = st.selectbox("Category", CATEGORIES)
with col3:
    amount = st.number_input("Amount (€)", min_value=0.0, step=0.01)
with col4:
    description = st.text_input("Description")

if st.button("💾 Save Expense"):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expenses (date, category, amount, description)
        VALUES (?, ?, ?, ?)
    """, (str(date), category, amount, description))
    conn.commit()
    conn.close()
    st.success("Expense saved!")
    st.rerun()

st.divider()

#Add paid bill
st.subheader("Add Paid Bill")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    bill_date = st.date_input("Bill Date")
with col2:
    bill_category = st.selectbox("Bill Category", CATEGORIES, key="bill_cat")
with col3:
    bill_amount = st.number_input("Amount (€)", min_value=0.0, step=0.01, key="bill_amt")
with col4:
    bill_description = st.text_input("Description", key="bill_desc")
with col5:
    bill_paid = st.checkbox("Paid", value=True)

if st.button("💾 Save Bill"):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO paid_bills (date, category, amount, description, paid)
        VALUES (?, ?, ?, ?, ?)
    """, (str(bill_date), bill_category, bill_amount, bill_description, int(bill_paid)))
    conn.commit()
    conn.close()
    st.success("Bill saved!")
    st.rerun()

st.divider()

#Load data
conn = create_connection()
expenses_df = pd.read_sql_query(
    "SELECT * FROM expenses WHERE category != 'Lebensmittel' ORDER BY date", conn)
bills_df = pd.read_sql_query("SELECT * FROM paid_bills ORDER BY date DESC", conn)
conn.close()

#Metrics
st.subheader("📊 Overview")
col1, col2, col3 = st.columns(3)

with col1:
    total = expenses_df["amount"].sum()
    st.metric("Total Expenses", f"€{total:.2f}")

with col2:
    total_paid = bills_df[bills_df["paid"] == 1]["amount"].sum()
    st.metric("Total Bills Paid", f"€{total_paid:.2f}")

with col3:
    total_unpaid = bills_df[bills_df["paid"] == 0]["amount"].sum()
    st.metric("Unpaid Bills", f"€{total_unpaid:.2f}")

st.divider()

#Charts
if not expenses_df.empty:
    st.subheader("📈 Charts")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.pie(expenses_df, values="amount", names="category",
                     title="Expenses by Category",
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(expenses_df, x="category", y="amount",
                     title="Expenses by Category (Bar)",
                     color="category",
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)

st.divider()

#Paid bills table
st.subheader("📋 Paid Bills History")

if bills_df.empty:
    st.info("No bills logged yet. Add your first bill above.")
else:
    def highlight_paid(row):
        if row["paid"] == 1:
            return ["background-color: #1a472a"] * len(row)
        else:
            return ["background-color: #4a1a1a"] * len(row)

    st.dataframe(
        bills_df.style.apply(highlight_paid, axis=1),
        use_container_width=True
    )

st.divider()

