import streamlit as st
import pandas as pd
import os
import base64
from database import create_connection, create_tables

create_tables()

st.set_page_config(page_title="Contracts", page_icon="📄", layout="wide")
st.title("📄 Contracts")
st.divider()

CONTRACT_TYPES = ["WiFi", "Gas", "Electricity", "Rent", "Insurance", "Other"]

#Upload contract
st.subheader("Upload New Contract")

col1, col2, col3 = st.columns(3)

with col1:
    contract_type = st.selectbox("Contract Type", CONTRACT_TYPES)
with col2:
    notes = st.text_input("Notes (optional)")
with col3:
    uploaded_file = st.file_uploader("Upload File", type=["pdf", "png", "jpg", "jpeg"])

if st.button("💾 Save Contract") and uploaded_file:
    os.makedirs("contracts", exist_ok=True)
    file_path = os.path.join("contracts", f"{contract_type}_{uploaded_file.name}")

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO contracts (date, contract_type, file_path, notes)
        VALUES (?, ?, ?, ?)
    """, (pd.Timestamp.now().strftime("%Y-%m-%d"), contract_type, file_path, notes))
    conn.commit()
    conn.close()
    st.success(f"{contract_type} contract saved!")
    st.rerun()

st.divider()

#Load contracts
conn = create_connection()
contracts_df = pd.read_sql_query("SELECT * FROM contracts ORDER BY date DESC", conn)
conn.close()

if contracts_df.empty:
    st.info("No contracts uploaded yet. Upload your first one above.")
else:
    st.subheader("📋 Your Contracts")

    for _, row in contracts_df.iterrows():
        with st.expander(f"📄 {row['contract_type']} — {row['date']} {f'| {row[chr(110)+chr(111)+chr(116)+chr(101)+chr(115)]}' if row['notes'] else ''}"):
            col1, col2 = st.columns([3, 1])

            with col1:
                file_path = row["file_path"]

                if os.path.exists(file_path):
                    # PDF preview
                    if file_path.endswith(".pdf"):
                        with open(file_path, "rb") as f:
                            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600px"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)

                    # Image preview
                    elif file_path.endswith((".png", ".jpg", ".jpeg")):
                        st.image(file_path, use_column_width=True)
                else:
                    st.warning("File not found on disk.")

            with col2:
                st.write(f"**Type:** {row['contract_type']}")
                st.write(f"**Uploaded:** {row['date']}")
                if row["notes"]:
                    st.write(f"**Notes:** {row['notes']}")

                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download",
                            data=f,
                            file_name=os.path.basename(file_path),
                            mime="application/octet-stream"
                        )