import streamlit as st
import pandas as pd
from datetime import datetime
from database import create_connection, create_tables

create_tables()

st.set_page_config(page_title="Edit & Manage", page_icon="✏️", layout="wide")
st.title("✏️ Edit & Manage Data")
st.divider()

TABLE_LABELS = {
    "energy": "⚡ Energy",
    "expenses": "💶 Expenses",
    "internet_speed": "🌐 Internet Speed",
    "paid_bills": "💸 Paid Bills",
    "contracts": "📄 Contracts"
}

CATEGORIES = ["Miete", "Strom", "Gas", "Internet", "Versicherung", "Transport", "Sonstiges"]
CONTRACT_TYPES = ["WiFi", "Gas", "Electricity", "Rent", "Insurance", "Other"]

def log_change(table_name, entry_id, field, old_value, new_value):
    if str(old_value) != str(new_value):
        conn = create_connection()
        conn.execute("""
            INSERT INTO edit_history (timestamp, table_name, entry_id, field_changed, old_value, new_value)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), table_name, entry_id, field, str(old_value), str(new_value)))
        conn.commit()
        conn.close()

#Table selector
    "Select Table",
    list(TABLE_LABELS.keys()),
    format_func=lambda x: TABLE_LABELS[x]
)

conn = create_connection()
df = pd.read_sql_query(f"SELECT * FROM {selected_table} ORDER BY date DESC", conn)
conn.close()

if df.empty:
    st.warning("No entries found in this table.")
    st.stop()

st.divider()

#Tabs
tab1, tab2, tab3 = st.tabs(["✏️ Edit Entry", "🗑️ Delete Entries", "📋 Edit History"])


#Edit Tab

with tab1:
    st.subheader("Select Entry to Edit")

    labels = []
    for _, row in df.iterrows():
        if selected_table == "energy":
            labels.append(f"ID {row['id']} | {row['date']} | Gas: {row['gas_reading']} m³ | Elec: {row['electricity_reading']} kWh")
        elif selected_table == "expenses":
            labels.append(f"ID {row['id']} | {row['date']} | {row['category']} | €{row['amount']}")
        elif selected_table == "internet_speed":
            labels.append(f"ID {row['id']} | {row['date']} | ↓{row['download']} Mbps ↑{row['upload']} Mbps | Ping: {row['ping']} ms")
        elif selected_table == "paid_bills":
            labels.append(f"ID {row['id']} | {row['date']} | {row['category']} | €{row['amount']} | {'✅ Paid' if row['paid'] else '❌ Unpaid'}")
        elif selected_table == "contracts":
            labels.append(f"ID {row['id']} | {row['contract_type']} | Started: {row['date']} | Expires: {row.get('expiry_date', 'N/A')}")

    selected_label = st.selectbox("Select Entry", labels)
    selected_id = int(selected_label.split("ID ")[1].split(" |")[0])
    selected_row = df[df["id"] == selected_id].iloc[0]

    st.divider()
    st.subheader(f"Editing ID {selected_id}")

    #Energy
    if selected_table == "energy":
        col1, col2 = st.columns(2)
        with col1:
            date = st.text_input("Date", value=selected_row["date"])
            gas = st.number_input("Gas Reading (m³)", value=float(selected_row["gas_reading"] or 0), step=0.1)
        with col2:
            elec = st.number_input("Electricity Reading (kWh)", value=float(selected_row["electricity_reading"] or 0), step=0.1)
            kwh = st.number_input("Power Used This Month (kWh)", value=float(selected_row["electricity_kwh"] or 0), step=0.1)
        notes = st.text_input("Notes", value=str(selected_row["notes"] or ""))

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save Changes", type="primary"):
                log_change(selected_table, selected_id, "date", selected_row["date"], date)
                log_change(selected_table, selected_id, "gas_reading", selected_row["gas_reading"], gas)
                log_change(selected_table, selected_id, "electricity_reading", selected_row["electricity_reading"], elec)
                log_change(selected_table, selected_id, "electricity_kwh", selected_row["electricity_kwh"], kwh)
                log_change(selected_table, selected_id, "notes", selected_row["notes"], notes)
                conn = create_connection()
                conn.execute("""
                    UPDATE energy SET date=?, gas_reading=?, electricity_reading=?, electricity_kwh=?, notes=?
                    WHERE id=?
                """, (date, gas, elec, kwh, notes, selected_id))
                conn.commit()
                conn.close()
                st.success(f"✅ Entry ID {selected_id} updated!")
                st.rerun()
        with col2:
            if st.button("❌ Cancel"):
                st.info("Changes cancelled — nothing was saved.")
                st.rerun()

    #Expenses
    elif selected_table == "expenses":
        col1, col2 = st.columns(2)
        with col1:
            date = st.text_input("Date", value=selected_row["date"])
            category = st.selectbox("Category", CATEGORIES,
                                    index=CATEGORIES.index(selected_row["category"])
                                    if selected_row["category"] in CATEGORIES else 0)
        with col2:
            amount = st.number_input("Amount (€)", value=float(selected_row["amount"] or 0), step=0.01)
            description = st.text_input("Description", value=str(selected_row["description"] or ""))

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save Changes", type="primary"):
                log_change(selected_table, selected_id, "date", selected_row["date"], date)
                log_change(selected_table, selected_id, "category", selected_row["category"], category)
                log_change(selected_table, selected_id, "amount", selected_row["amount"], amount)
                log_change(selected_table, selected_id, "description", selected_row["description"], description)
                conn = create_connection()
                conn.execute("""
                    UPDATE expenses SET date=?, category=?, amount=?, description=?
                    WHERE id=?
                """, (date, category, amount, description, selected_id))
                conn.commit()
                conn.close()
                st.success(f"✅ Entry ID {selected_id} updated!")
                st.rerun()
        with col2:
            if st.button("❌ Cancel"):
                st.info("Changes cancelled — nothing was saved.")
                st.rerun()

    #Internet speed
    elif selected_table == "internet_speed":
        col1, col2 = st.columns(2)
        with col1:
            date = st.text_input("Date", value=selected_row["date"])
            download = st.number_input("Download (Mbps)", value=float(selected_row["download"] or 0), step=0.1)
        with col2:
            upload = st.number_input("Upload (Mbps)", value=float(selected_row["upload"] or 0), step=0.1)
            ping = st.number_input("Ping (ms)", value=float(selected_row["ping"] or 0), step=0.1)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save Changes", type="primary"):
                log_change(selected_table, selected_id, "date", selected_row["date"], date)
                log_change(selected_table, selected_id, "download", selected_row["download"], download)
                log_change(selected_table, selected_id, "upload", selected_row["upload"], upload)
                log_change(selected_table, selected_id, "ping", selected_row["ping"], ping)
                conn = create_connection()
                conn.execute("""
                    UPDATE internet_speed SET date=?, download=?, upload=?, ping=?
                    WHERE id=?
                """, (date, download, upload, ping, selected_id))
                conn.commit()
                conn.close()
                st.success(f"✅ Entry ID {selected_id} updated!")
                st.rerun()
        with col2:
            if st.button("❌ Cancel"):
                st.info("Changes cancelled — nothing was saved.")
                st.rerun()

    #Paid bills
    elif selected_table == "paid_bills":
        col1, col2 = st.columns(2)
        with col1:
            date = st.text_input("Date", value=selected_row["date"])
            category = st.selectbox("Category", CATEGORIES,
                                    index=CATEGORIES.index(selected_row["category"])
                                    if selected_row["category"] in CATEGORIES else 0)
        with col2:
            amount = st.number_input("Amount (€)", value=float(selected_row["amount"] or 0), step=0.01)
            description = st.text_input("Description", value=str(selected_row["description"] or ""))
        paid = st.checkbox("Paid ✅", value=bool(selected_row["paid"]))

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save Changes", type="primary"):
                log_change(selected_table, selected_id, "date", selected_row["date"], date)
                log_change(selected_table, selected_id, "category", selected_row["category"], category)
                log_change(selected_table, selected_id, "amount", selected_row["amount"], amount)
                log_change(selected_table, selected_id, "description", selected_row["description"], description)
                log_change(selected_table, selected_id, "paid", selected_row["paid"], int(paid))
                conn = create_connection()
                conn.execute("""
                    UPDATE paid_bills SET date=?, category=?, amount=?, description=?, paid=?
                    WHERE id=?
                """, (date, category, amount, description, int(paid), selected_id))
                conn.commit()
                conn.close()
                st.success(f"✅ Entry ID {selected_id} updated!")
                st.rerun()
        with col2:
            if st.button("❌ Cancel"):
                st.info("Changes cancelled — nothing was saved.")
                st.rerun()

    #Contracts
    elif selected_table == "contracts":
        col1, col2 = st.columns(2)
        with col1:
            contract_type = st.selectbox("Contract Type", CONTRACT_TYPES,
                                         index=CONTRACT_TYPES.index(selected_row["contract_type"])
                                         if selected_row["contract_type"] in CONTRACT_TYPES else 0)
            start_date = st.text_input("Start Date", value=str(selected_row["date"]))
        with col2:
            expiry_date = st.text_input("Expiry Date (YYYY-MM-DD)", value=str(selected_row["expiry_date"] or ""))
            notes = st.text_input("Notes", value=str(selected_row["notes"] or ""))

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save Changes", type="primary"):
                log_change(selected_table, selected_id, "contract_type", selected_row["contract_type"], contract_type)
                log_change(selected_table, selected_id, "date", selected_row["date"], start_date)
                log_change(selected_table, selected_id, "expiry_date", selected_row["expiry_date"], expiry_date)
                log_change(selected_table, selected_id, "notes", selected_row["notes"], notes)
                conn = create_connection()
                conn.execute("""
                    UPDATE contracts SET contract_type=?, date=?, expiry_date=?, notes=?
                    WHERE id=?
                """, (contract_type, start_date, expiry_date, notes, selected_id))
                conn.commit()
                conn.close()
                st.success(f"✅ Entry ID {selected_id} updated!")
                st.rerun()
        with col2:
            if st.button("❌ Cancel"):
                st.info("Changes cancelled — nothing was saved.")
                st.rerun()


#Deletion Tab
with tab2:
    st.subheader("Select Entries to Delete")
    st.warning("⚠️ Deleted entries cannot be recovered.")

    to_delete = []

    for _, row in df.iterrows():
        if selected_table == "energy":
            label = f"ID {row['id']} | {row['date']} | Gas: {row['gas_reading']} m³ | Elec: {row['electricity_reading']} kWh"
        elif selected_table == "expenses":
            label = f"ID {row['id']} | {row['date']} | {row['category']} | €{row['amount']}"
        elif selected_table == "internet_speed":
            label = f"ID {row['id']} | {row['date']} | ↓{row['download']} Mbps | Ping: {row['ping']} ms"
        elif selected_table == "paid_bills":
            label = f"ID {row['id']} | {row['date']} | {row['category']} | €{row['amount']} | {'✅ Paid' if row['paid'] else '❌ Unpaid'}"
        elif selected_table == "contracts":
            label = f"ID {row['id']} | {row['contract_type']} | Started: {row['date']}"

        if st.checkbox(label, key=f"del_{row['id']}"):
            to_delete.append(row['id'])

    st.divider()

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🗑️ Delete Selected", type="primary", disabled=len(to_delete) == 0):
            conn = create_connection()
            for entry_id in to_delete:
                conn.execute(f"DELETE FROM {selected_table} WHERE id=?", (entry_id,))
            conn.commit()
            conn.close()
            st.success(f"✅ Deleted {len(to_delete)} entries!")
            st.rerun()
    with col2:
        if len(to_delete) > 0:
            st.info(f"{len(to_delete)} entries selected for deletion")
        else:
            st.caption("No entries selected")


#Editing Tab
with tab3:
    st.subheader("📋 Edit History")

    conn = create_connection()
    history_df = pd.read_sql_query("""
        SELECT * FROM edit_history ORDER BY timestamp DESC
    """, conn)
    conn.close()

    if history_df.empty:
        st.info("No edits made yet. History will appear here after you edit entries.")
    else:
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            filter_table = st.selectbox("Filter by Table",
                                        ["All"] + list(history_df["table_name"].unique()))
        with col2:
            filter_field = st.selectbox("Filter by Field",
                                        ["All"] + list(history_df["field_changed"].unique()))

        filtered = history_df.copy()
        if filter_table != "All":
            filtered = filtered[filtered["table_name"] == filter_table]
        if filter_field != "All":
            filtered = filtered[filtered["field_changed"] == filter_field]

        st.dataframe(
            filtered[["timestamp", "table_name", "entry_id", "field_changed", "old_value", "new_value"]],
            use_container_width=True
        )

        st.divider()
        st.caption(f"Total edits logged: {len(history_df)}")

        if st.button("🗑️ Clear All History"):
            conn = create_connection()
            conn.execute("DELETE FROM edit_history")
            conn.commit()
            conn.close()
            st.success("Edit history cleared!")
            st.rerun()