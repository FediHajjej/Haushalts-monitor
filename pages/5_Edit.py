import streamlit as st
import pandas as pd
from database import create_connection, create_tables

create_tables()

st.set_page_config(page_title="Edit", page_icon="✏️", layout="wide")
st.title("✏️ Edit Entries")
st.divider()

table = st.selectbox("Select Table to Edit", [
    "energy", "expenses", "internet_speed", "paid_bills"
])

conn = create_connection()
df = pd.read_sql_query(f"SELECT * FROM {table} ORDER BY date DESC", conn)
conn.close()

if df.empty:
    st.warning("No entries found in this table.")
else:
    st.subheader(f"Select an entry from **{table}**")

    #Dropdown Labels
    labels = []
    for _, row in df.iterrows():
        if table == "energy":
            labels.append(f"ID {row['id']} — {row['date']} | Gas: {row['gas_reading']} | Elec: {row['electricity_reading']}")
        elif table == "expenses":
            labels.append(f"ID {row['id']} — {row['date']} | {row['category']} | €{row['amount']}")
        elif table == "internet_speed":
            labels.append(f"ID {row['id']} — {row['date']} | ↓{row['download']} ↑{row['upload']} Ping:{row['ping']}")
        elif table == "paid_bills":
            labels.append(f"ID {row['id']} — {row['date']} | {row['category']} | €{row['amount']}")

    selected_label = st.selectbox("Select Entry", labels)
    selected_id = int(selected_label.split("ID ")[1].split(" —")[0])
    selected_row = df[df["id"] == selected_id].iloc[0]

    st.divider()
    st.subheader("Edit Values")

    #Energy Form
    if table == "energy":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            date = st.text_input("Date", value=selected_row["date"])
        with col2:
            gas = st.number_input("Gas Reading", value=float(selected_row["gas_reading"] or 0))
        with col3:
            elec = st.number_input("Electricity Reading", value=float(selected_row["electricity_reading"] or 0))
        with col4:
            kwh = st.number_input("Power Used (kWh)", value=float(selected_row["electricity_kwh"] or 0))
        notes = st.text_input("Notes", value=str(selected_row["notes"] or ""))

        if st.button("💾 Save Changes"):
            conn = create_connection()
            conn.execute("""
                UPDATE energy SET date=?, gas_reading=?, electricity_reading=?, electricity_kwh=?, notes=?
                WHERE id=?
            """, (date, gas, elec, kwh, notes, selected_id))
            conn.commit()
            conn.close()
            st.success("Entry updated!")
            st.rerun()

    #Expenses Form
    elif table == "expenses":
        CATEGORIES = ["Miete", "Strom", "Gas", "Internet", "Versicherung", "Transport", "Sonstiges"]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            date = st.text_input("Date", value=selected_row["date"])
        with col2:
            category = st.selectbox("Category", CATEGORIES,
                                    index=CATEGORIES.index(selected_row["category"])
                                    if selected_row["category"] in CATEGORIES else 0)
        with col3:
            amount = st.number_input("Amount (€)", value=float(selected_row["amount"] or 0))
        with col4:
            description = st.text_input("Description", value=str(selected_row["description"] or ""))

        if st.button("💾 Save Changes"):
            conn = create_connection()
            conn.execute("""
                UPDATE expenses SET date=?, category=?, amount=?, description=?
                WHERE id=?
            """, (date, category, amount, description, selected_id))
            conn.commit()
            conn.close()
            st.success("Entry updated!")
            st.rerun()

    #Internet speed Form
    elif table == "internet_speed":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            date = st.text_input("Date", value=selected_row["date"])
        with col2:
            download = st.number_input("Download (Mbps)", value=float(selected_row["download"] or 0))
        with col3:
            upload = st.number_input("Upload (Mbps)", value=float(selected_row["upload"] or 0))
        with col4:
            ping = st.number_input("Ping (ms)", value=float(selected_row["ping"] or 0))

        if st.button("💾 Save Changes"):
            conn = create_connection()
            conn.execute("""
                UPDATE internet_speed SET date=?, download=?, upload=?, ping=?
                WHERE id=?
            """, (date, download, upload, ping, selected_id))
            conn.commit()
            conn.close()
            st.success("Entry updated!")
            st.rerun()

    #Paid bills Form
    elif table == "paid_bills":
        CATEGORIES = ["Miete", "Strom", "Gas", "Internet", "Versicherung", "Transport", "Sonstiges"]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            date = st.text_input("Date", value=selected_row["date"])
        with col2:
            category = st.selectbox("Category", CATEGORIES,
                                    index=CATEGORIES.index(selected_row["category"])
                                    if selected_row["category"] in CATEGORIES else 0)
        with col3:
            amount = st.number_input("Amount (€)", value=float(selected_row["amount"] or 0))
        with col4:
            description = st.text_input("Description", value=str(selected_row["description"] or ""))
        paid = st.checkbox("Paid", value=bool(selected_row["paid"]))

        if st.button("💾 Save Changes"):
            conn = create_connection()
            conn.execute("""
                UPDATE paid_bills SET date=?, category=?, amount=?, description=?, paid=?
                WHERE id=?
            """, (date, category, amount, description, int(paid), selected_id))
            conn.commit()
            conn.close()
            st.success("Entry updated!")
            st.rerun()

    st.divider()

    #Delete Entry
    st.subheader("🗑️ Delete Entry")
    st.warning("This action cannot be undone.")

    if st.button("🗑️ Delete Selected Entry"):
        conn = create_connection()
        conn.execute(f"DELETE FROM {table} WHERE id=?", (selected_id,))
        conn.commit()
        conn.close()
        st.success("Entry deleted!")
        st.rerun()