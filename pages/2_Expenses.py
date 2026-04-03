import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from database import create_connection, create_tables

create_tables()

st.set_page_config(page_title="Expenses", page_icon="💶", layout="wide")
st.title("💶 Expenses & Bills")
st.divider()

CATEGORIES = ["Miete", "Strom", "Gas", "Internet", "Versicherung", "Transport", "Sonstiges"]

# Default budgets
DEFAULT_BUDGETS = {
    "Miete": 700,
    "Strom": 100,
    "Gas": 150,
    "Internet": 50,
    "Versicherung": 60,
    "Transport": 60,
    "Sonstiges": 100
}

# ─── Load data ────────────────────────────────────────────
conn = create_connection()
expenses_df = pd.read_sql_query(
    "SELECT * FROM expenses WHERE category != 'Lebensmittel' ORDER BY date DESC", conn)
bills_df = pd.read_sql_query("SELECT * FROM paid_bills ORDER BY date DESC", conn)
conn.close()

expenses_df["date"] = pd.to_datetime(expenses_df["date"])
bills_df["date"] = pd.to_datetime(bills_df["date"])

today = pd.Timestamp.now()
this_month = today.strftime("%Y-%m")
last_month = (today - timedelta(days=30)).strftime("%Y-%m")

monthly_expenses = expenses_df[expenses_df["date"].dt.strftime("%Y-%m") == this_month]
last_month_expenses = expenses_df[expenses_df["date"].dt.strftime("%Y-%m") == last_month]

# ─── Tabs ─────────────────────────────────────────────────
tab1, tab2, tab3, tab4,  = st.tabs([
    "📊 Overview",
    "💰 Budget",
    "📋 Bills",
    "🔍 Search & Filter",
])

# ══════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════
with tab1:
    # ─── Top metrics ──────────────────────────────────────
    st.subheader("📊 This Month at a Glance")

    col1, col2, col3, col4, col5 = st.columns(5)

    this_total = monthly_expenses["amount"].sum()
    last_total = last_month_expenses["amount"].sum()
    diff = this_total - last_total
    diff_pct = ((this_total - last_total) / last_total * 100) if last_total > 0 else 0

    with col1:
        st.metric("This Month", f"€{this_total:.2f}",
                  delta=f"{diff_pct:.1f}% vs last month",
                  delta_color="inverse")
    with col2:
        st.metric("Last Month", f"€{last_total:.2f}")
    with col3:
        avg_monthly = expenses_df.groupby(
            expenses_df["date"].dt.strftime("%Y-%m"))["amount"].sum().mean()
        st.metric("Monthly Average", f"€{avg_monthly:.2f}")
    with col4:
        unpaid = bills_df[bills_df["paid"] == 0]["amount"].sum()
        st.metric("⚠️ Unpaid Bills", f"€{unpaid:.2f}")
    with col5:
        total_ever = expenses_df["amount"].sum()
        st.metric("Total Ever Tracked", f"€{total_ever:.2f}")

    st.divider()

    # ─── Monthly breakdown chart ───────────────────────────
    st.subheader("📈 Monthly Spending Breakdown")

    monthly_grouped = expenses_df.copy()
    monthly_grouped["month"] = monthly_grouped["date"].dt.strftime("%Y-%m")
    monthly_chart = monthly_grouped.groupby(
        ["month", "category"])["amount"].sum().reset_index()

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(monthly_chart, x="month", y="amount", color="category",
                     title="Monthly Spending by Category",
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(monthly_chart, x="month", y="amount", color="category",
                      title="Category Trends Over Time",
                      markers=True,
                      color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        monthly_total = monthly_grouped.groupby("month")["amount"].sum().reset_index()
        fig = px.area(monthly_total, x="month", y="amount",
                      title="Total Monthly Spending",
                      color_discrete_sequence=["#00CC96"])
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        this_month_cat = monthly_expenses.groupby("category")["amount"].sum().reset_index()
        if not this_month_cat.empty:
            fig = px.pie(this_month_cat, values="amount", names="category",
                         title=f"This Month's Breakdown ({this_month})",
                         color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ─── Month over month comparison ──────────────────────
    st.subheader("📊 Month over Month Comparison")

    col1, col2 = st.columns(2)

    for cat in CATEGORIES:
        this_cat = monthly_expenses[monthly_expenses["category"] == cat]["amount"].sum()
        last_cat = last_month_expenses[last_month_expenses["category"] == cat]["amount"].sum()
        diff_cat = this_cat - last_cat
        diff_cat_pct = ((this_cat - last_cat) / last_cat * 100) if last_cat > 0 else 0

    comparison_data = []
    for cat in CATEGORIES:
        this_cat = monthly_expenses[monthly_expenses["category"] == cat]["amount"].sum()
        last_cat = last_month_expenses[last_month_expenses["category"] == cat]["amount"].sum()
        comparison_data.append({
            "Category": cat,
            "This Month": round(this_cat, 2),
            "Last Month": round(last_cat, 2),
            "Change (€)": round(this_cat - last_cat, 2),
            "Change (%)": round(((this_cat - last_cat) / last_cat * 100) if last_cat > 0 else 0, 1)
        })

    comp_df = pd.DataFrame(comparison_data)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Last Month", x=comp_df["Category"],
                             y=comp_df["Last Month"],
                             marker_color="#636EFA"))
        fig.add_trace(go.Bar(name="This Month", x=comp_df["Category"],
                             y=comp_df["This Month"],
                             marker_color="#EF553B"))
        fig.update_layout(barmode="group", title="This Month vs Last Month")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        def color_change(val):
            if isinstance(val, float) or isinstance(val, int):
                color = "red" if val > 0 else "green"
                return f"color: {color}"
            return ""

        st.dataframe(
            comp_df.style.applymap(color_change, subset=["Change (€)", "Change (%)"]),
            use_container_width=True
        )

# ══════════════════════════════════════════════════════════
# TAB 2 — BUDGET
# ══════════════════════════════════════════════════════════
with tab2:
    st.subheader("💰 Monthly Budget Manager")

    # Budget settings in sidebar-style expander
    with st.expander("⚙️ Set Monthly Budgets"):
        budgets = {}
        col1, col2 = st.columns(2)
        cats_left = CATEGORIES[:4]
        cats_right = CATEGORIES[4:]

        with col1:
            for cat in cats_left:
                budgets[cat] = st.number_input(
                    f"{cat} Budget (€)",
                    value=float(DEFAULT_BUDGETS.get(cat, 100)),
                    step=10.0,
                    key=f"budget_{cat}"
                )
        with col2:
            for cat in cats_right:
                budgets[cat] = st.number_input(
                    f"{cat} Budget (€)",
                    value=float(DEFAULT_BUDGETS.get(cat, 100)),
                    step=10.0,
                    key=f"budget_{cat}"
                )

    st.divider()
    st.subheader(f"📊 Budget Usage — {this_month}")

    total_budget = sum(budgets.values())
    total_spent = monthly_expenses["amount"].sum()
    total_pct = (total_spent / total_budget * 100) if total_budget > 0 else 0

    # Overall budget bar
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Budget", f"€{total_budget:.2f}")
    with col2:
        st.metric("Total Spent", f"€{total_spent:.2f}")
    with col3:
        remaining = total_budget - total_spent
        st.metric("Remaining", f"€{remaining:.2f}",
                  delta_color="normal")

    if total_pct >= 100:
        st.error(f"⚠️ Over budget! Spent {total_pct:.1f}% of total budget")
    elif total_pct >= 90:
        st.warning(f"🟡 At {total_pct:.1f}% of total budget")
    else:
        st.success(f"🟢 At {total_pct:.1f}% of total budget")

    st.progress(min(total_pct / 100, 1.0))
    st.divider()

    # Per category progress bars
    for cat in CATEGORIES:
        spent = monthly_expenses[monthly_expenses["category"] == cat]["amount"].sum()
        budget = budgets.get(cat, 100)
        pct = (spent / budget * 100) if budget > 0 else 0

        col1, col2, col3, col4 = st.columns([2, 1, 1, 3])
        with col1:
            st.write(f"**{cat}**")
        with col2:
            st.write(f"€{spent:.2f}")
        with col3:
            st.write(f"/ €{budget:.2f}")
        with col4:
            if pct >= 100:
                st.error(f"🔴 {pct:.0f}% — OVER BUDGET by €{spent - budget:.2f}")
                st.progress(1.0)
            elif pct >= 90:
                st.warning(f"🟡 {pct:.0f}%")
                st.progress(min(pct / 100, 1.0))
            elif pct >= 70:
                st.info(f"🔵 {pct:.0f}%")
                st.progress(min(pct / 100, 1.0))
            else:
                st.success(f"🟢 {pct:.0f}%")
                st.progress(min(pct / 100, 1.0))

    st.divider()

    # Budget chart
    budget_chart_data = []
    for cat in CATEGORIES:
        spent = monthly_expenses[monthly_expenses["category"] == cat]["amount"].sum()
        budget_chart_data.append({
            "Category": cat,
            "Spent": round(spent, 2),
            "Budget": budgets.get(cat, 100)
        })

    budget_df = pd.DataFrame(budget_chart_data)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Budget", x=budget_df["Category"],
                         y=budget_df["Budget"],
                         marker_color="#636EFA", opacity=0.5))
    fig.add_trace(go.Bar(name="Spent", x=budget_df["Category"],
                         y=budget_df["Spent"],
                         marker_color="#EF553B"))
    fig.update_layout(barmode="overlay", title="Budget vs Actual Spending")
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 3 — BILLS
# ══════════════════════════════════════════════════════════
with tab3:
    st.subheader("📋 Bills Manager")

    # ─── Two column layout ────────────────────────────────
    col_left, col_right = st.columns(2)

    # ─── LEFT — Add new bill ──────────────────────────────
    with col_left:
        st.markdown("### ➕ Add New Bill")
        with st.form("add_bill_form"):
            bill_date = st.date_input("Date", value=date.today())
            bill_cat = st.selectbox("Category", CATEGORIES)
            bill_amt = st.number_input("Amount (€)", min_value=0.0, step=0.01)
            bill_desc = st.text_input("Description")
            bill_paid = st.checkbox("Already Paid ✅", value=True)

            if st.form_submit_button("💾 Save Bill", type="primary"):
                conn = create_connection()
                conn.execute("""
                    INSERT INTO paid_bills (date, category, amount, description, paid)
                    VALUES (?, ?, ?, ?, ?)
                """, (str(bill_date), bill_cat, bill_amt, bill_desc, int(bill_paid)))
                conn.commit()
                conn.close()
                st.success("Bill saved!")
                st.rerun()

    # ─── RIGHT — Add upcoming expense ────────────────────
    with col_right:
        st.markdown("### 📅 Add Upcoming Expense")
        with st.form("add_upcoming_form"):
            up_cat = st.selectbox("Category", CATEGORIES, key="up_cat")
            up_amt = st.number_input("Amount (€)", min_value=0.0, step=0.01, key="up_amt")
            up_desc = st.text_input("Description", key="up_desc")
            up_due = st.date_input("Due Date", value=date.today() + timedelta(days=7))

            if st.form_submit_button("💾 Save Upcoming Expense", type="primary"):
                conn = create_connection()
                conn.execute("""
                    INSERT INTO upcoming_expenses (category, amount, description, due_date, reminder_sent, paid)
                    VALUES (?, ?, ?, ?, 0, 0)
                """, (up_cat, up_amt, up_desc, str(up_due)))
                conn.commit()
                conn.close()
                st.success("Upcoming expense saved!")
                st.rerun()

    st.divider()

    # ─── Upcoming expenses ────────────────────────────────
    conn = create_connection()
    upcoming_df = pd.read_sql_query(
        "SELECT * FROM upcoming_expenses WHERE paid=0 ORDER BY due_date ASC", conn)
    conn.close()

    if not upcoming_df.empty:
        st.subheader("📅 Upcoming Expenses")

        today_date = date.today()

        for _, row in upcoming_df.iterrows():
            due = datetime.strptime(row["due_date"], "%Y-%m-%d").date()
            days_left = (due - today_date).days

            col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 2, 2, 1, 1])

            with col1:
                st.write(f"**{row['category']}**")
            with col2:
                st.write(f"€{row['amount']:.2f}")
            with col3:
                st.write(row["description"] or "")
            with col4:
                if days_left < 0:
                    st.error(f"🔴 Overdue by {abs(days_left)} days")
                elif days_left <= 7:
                    st.warning(f"🟡 Due in {days_left} days")
                elif days_left <= 30:
                    st.info(f"🔵 Due in {days_left} days")
                else:
                    st.success(f"🟢 Due in {days_left} days")
            with col5:
                if st.button("✅ Paid", key=f"up_paid_{row['id']}"):
                    conn = create_connection()
                    conn.execute("UPDATE upcoming_expenses SET paid=1 WHERE id=?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.success("Marked as paid!")
                    st.rerun()
            with col6:
                if st.button("🗑️", key=f"up_del_{row['id']}"):
                    conn = create_connection()
                    conn.execute("DELETE FROM upcoming_expenses WHERE id=?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()

        # ─── Send reminders button ────────────────────────
        st.divider()
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("📧 Send Reminder Email Now", type="primary"):
                from notifications import check_upcoming_expenses
                check_upcoming_expenses()
                st.success("Reminder email sent!")
        with col2:
            st.caption("Sends email for all bills due within 7 days or overdue")

        st.divider()

    # ─── Bills summary ────────────────────────────────────
    st.subheader("📊 Bills Summary")

    col1, col2, col3 = st.columns(3)
    with col1:
        total_paid = bills_df[bills_df["paid"] == 1]["amount"].sum()
        st.metric("✅ Total Paid", f"€{total_paid:.2f}")
    with col2:
        total_unpaid = bills_df[bills_df["paid"] == 0]["amount"].sum()
        st.metric("❌ Total Unpaid", f"€{total_unpaid:.2f}")
    with col3:
        overdue = bills_df[
            (bills_df["paid"] == 0) &
            (bills_df["date"] < pd.Timestamp.now() - timedelta(days=30))
        ]
        st.metric("⚠️ Overdue Bills", len(overdue))

    st.divider()

    # ─── Unpaid bills ─────────────────────────────────────
    unpaid_bills = bills_df[bills_df["paid"] == 0].copy()
    if not unpaid_bills.empty:
        st.subheader("❌ Unpaid Bills")
        for _, row in unpaid_bills.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 2, 1])
            with col1:
                st.write(f"**{row['category']}**")
            with col2:
                st.write(str(row['date'])[:10])
            with col3:
                st.write(f"€{row['amount']:.2f}")
            with col4:
                st.write(row['description'] or "")
            with col5:
                if st.button("✅ Mark Paid", key=f"pay_{row['id']}"):
                    conn = create_connection()
                    conn.execute("UPDATE paid_bills SET paid=1 WHERE id=?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.success("Marked as paid!")
                    st.rerun()
        st.divider()

    # ─── Paid bills history ───────────────────────────────
    st.subheader("✅ Paid Bills History")
    paid_bills = bills_df[bills_df["paid"] == 1].copy()

    if paid_bills.empty:
        st.info("No paid bills yet.")
    else:
        month_filter = st.selectbox(
            "Filter by Month",
            ["All"] + sorted(
                paid_bills["date"].dt.strftime("%Y-%m").unique().tolist(),
                reverse=True
            )
        )

        if month_filter != "All":
            paid_bills = paid_bills[
                paid_bills["date"].dt.strftime("%Y-%m") == month_filter]

        st.dataframe(
            paid_bills[["date", "category", "amount", "description"]].rename(
                columns={"date": "Date", "category": "Category",
                         "amount": "Amount (€)", "description": "Description"}
            ),
            use_container_width=True
        )

# ══════════════════════════════════════════════════════════
# TAB 4 — SEARCH & FILTER
# ══════════════════════════════════════════════════════════
with tab4:
    st.subheader("🔍 Search & Filter Expenses")

    col1, col2, col3 = st.columns(3)

    with col1:
        search_cat = st.multiselect("Category", CATEGORIES, default=CATEGORIES)
    with col2:
        date_from = st.date_input("From", value=date.today() - timedelta(days=365))
    with col3:
        date_to = st.date_input("To", value=date.today())

    search_desc = st.text_input("Search description...")

    filtered = expenses_df[
        (expenses_df["category"].isin(search_cat)) &
        (expenses_df["date"] >= pd.Timestamp(date_from)) &
        (expenses_df["date"] <= pd.Timestamp(date_to))
    ]

    if search_desc:
        filtered = filtered[filtered["description"].str.contains(
            search_desc, case=False, na=False)]

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Results Found", len(filtered))
    with col2:
        st.metric("Total Amount", f"€{filtered['amount'].sum():.2f}")

    st.dataframe(
        filtered[["date", "category", "amount", "description"]].rename(
            columns={"date": "Date", "category": "Category",
                     "amount": "Amount (€)", "description": "Description"}
        ),
        use_container_width=True
    )

    # CSV Export
    st.divider()
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Export to CSV",
        data=csv,
        file_name=f"expenses_{date_from}_{date_to}.csv",
        mime="text/csv"
    )

