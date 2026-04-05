import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import os
import base64
from database import create_connection, create_tables

create_tables()

st.set_page_config(page_title="Income", page_icon="💰", layout="wide")
st.title("💰 Income Tracker")
st.divider()



conn = create_connection()
income_df = pd.read_sql_query("SELECT * FROM income ORDER BY date DESC", conn)
expenses_df = pd.read_sql_query(
    "SELECT * FROM expenses WHERE category != 'Lebensmittel' ORDER BY date DESC", conn)

try:
    people_df = pd.read_sql_query("SELECT * FROM people ORDER BY name", conn)
    sources_df = pd.read_sql_query("SELECT * FROM income_sources ORDER BY name", conn)
    people_list = people_df["name"].tolist()
    sources_list = sources_df["name"].tolist()
except:
    people_list = []
    sources_list = []

try:
    recurring_df = pd.read_sql_query(
        "SELECT * FROM recurring_income WHERE active=1 ORDER BY person", conn)
except:
    recurring_df = pd.DataFrame()

try:
    payslips_df = pd.read_sql_query(
        "SELECT * FROM payslips ORDER BY month DESC", conn)
except:
    payslips_df = pd.DataFrame()

try:
    jobs_df = pd.read_sql_query("SELECT * FROM job_profiles ORDER BY person", conn)
except:
    jobs_df = pd.DataFrame()

conn.close()

if not income_df.empty:
    income_df["date"] = pd.to_datetime(income_df["date"])
if not expenses_df.empty:
    expenses_df["date"] = pd.to_datetime(expenses_df["date"])

today = pd.Timestamp.now()
this_month = today.strftime("%Y-%m")
last_month = (today - timedelta(days=30)).strftime("%Y-%m")

#Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview",
    "👫 By Person",
    "📈 Trends",
    "🎯 Savings",
    "🔄 Recurring",
    "⚙️ Manage"
])

#Overview
with tab1:

    st.subheader("➕ Add Income Entry")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        inc_date = st.date_input("Date", value=date.today())
    with col2:
        inc_person = st.selectbox(
            "Person", people_list if people_list else ["Add person in Manage tab"])
    with col3:
        inc_source = st.selectbox(
            "Source", sources_list if sources_list else ["Add source in Manage tab"])
    with col4:
        inc_amount = st.number_input("Amount (€)", min_value=0.0, step=0.01)
    with col5:
        inc_desc = st.text_input("Description")

    if st.button("💾 Save Income", type="primary"):
        if inc_amount > 0:
            conn = create_connection()
            conn.execute("""
                INSERT INTO income (date, person, source, amount, description)
                VALUES (?, ?, ?, ?, ?)
            """, (str(inc_date), inc_person, inc_source, inc_amount, inc_desc))
            conn.commit()
            conn.close()
            st.success("Income saved!")
            st.rerun()
        else:
            st.warning("Enter an amount greater than 0")

    st.divider()

    if income_df.empty:
        st.warning("No income data yet. Add your first entry above.")
        st.stop()


#Metrics
    st.subheader("This Month at a Glance")

    monthly_income = income_df[income_df["date"].dt.strftime("%Y-%m") == this_month]
    last_month_income = income_df[income_df["date"].dt.strftime("%Y-%m") == last_month]
    monthly_expenses = expenses_df[
        expenses_df["date"].dt.strftime("%Y-%m") == this_month] if not expenses_df.empty else pd.DataFrame()

    total_income_this = monthly_income["amount"].sum()
    total_income_last = last_month_income["amount"].sum()
    total_expenses_this = monthly_expenses["amount"].sum() if not monthly_expenses.empty else 0
    net_cashflow = total_income_this - total_expenses_this
    savings_rate = (net_cashflow / total_income_this * 100) if total_income_this > 0 else 0
    income_change = ((total_income_this - total_income_last) / total_income_last * 100) if total_income_last > 0 else 0
    avg_monthly = income_df.groupby(
        income_df["date"].dt.strftime("%Y-%m"))["amount"].sum().mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Income", f"€{total_income_this:.2f}",
                  delta=f"{income_change:.1f}% vs last month")
    with col2:
        st.metric("Total Expenses", f"€{total_expenses_this:.2f}")
    with col3:
        st.metric("Net Cash Flow", f"€{net_cashflow:.2f}")
    with col4:
        st.metric("Savings Rate", f"{savings_rate:.1f}%")
    with col5:
        st.metric("Avg Monthly Income", f"€{avg_monthly:.2f}")

    st.divider()


#Charts
    st.subheader("Income vs Expenses")

    monthly_inc = income_df.copy()
    monthly_inc["month"] = monthly_inc["date"].dt.strftime("%Y-%m")
    monthly_inc_grouped = monthly_inc.groupby("month")["amount"].sum().reset_index()
    monthly_inc_grouped.columns = ["month", "income"]

    if not expenses_df.empty:
        monthly_exp = expenses_df.copy()
        monthly_exp["month"] = monthly_exp["date"].dt.strftime("%Y-%m")
        monthly_exp_grouped = monthly_exp.groupby(
            "month")["amount"].sum().reset_index()
        monthly_exp_grouped.columns = ["month", "expenses"]
        combined = monthly_inc_grouped.merge(
            monthly_exp_grouped, on="month", how="outer").fillna(0)
    else:
        combined = monthly_inc_grouped.copy()
        combined["expenses"] = 0

    combined["savings"] = combined["income"] - combined["expenses"]
    combined["savings_rate"] = (
        combined["savings"] / combined["income"] * 100).round(1)

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Income", x=combined["month"], y=combined["income"],
            marker_color="#00CC96"))
        fig.add_trace(go.Bar(
            name="Expenses", x=combined["month"], y=combined["expenses"],
            marker_color="#EF553B"))
        fig.update_layout(barmode="group",
                          title="Monthly Income vs Expenses",
                          xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        colors = ["#00CC96" if s >= 0 else "#EF553B" for s in combined["savings"]]
        fig = go.Figure(go.Bar(
            x=combined["month"], y=combined["savings"],
            marker_color=colors))
        fig.update_layout(title="Monthly Net Savings", xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(combined, x="month", y="savings_rate",
                      title="Savings Rate Over Time (%)",
                      markers=True,
                      color_discrete_sequence=["#00CC96"])
        fig.add_hline(y=20, line_dash="dash",
                      annotation_text="20% target",
                      line_color="#FFD700")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=combined["month"], y=combined["income"],
            name="Income", fill="tozeroy", mode="lines",
            line=dict(color="#00CC96")))
        fig.add_trace(go.Scatter(
            x=combined["month"], y=combined["expenses"],
            name="Expenses", fill="tozeroy", mode="lines",
            line=dict(color="#EF553B"), opacity=0.7))
        fig.update_layout(title="Income vs Expenses Area",
                          xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()


#general stats

    st.subheader("All Time Stats")

    col1, col2, col3, col4 = st.columns(4)

    total_ever = income_df["amount"].sum()
    total_exp_ever = expenses_df["amount"].sum() if not expenses_df.empty else 0
    total_saved = total_ever - total_exp_ever
    best_month = monthly_inc_grouped.loc[monthly_inc_grouped["income"].idxmax()]
    avg_savings_rate = combined["savings_rate"].mean()

    with col1:
        st.metric("Total Income Ever", f"€{total_ever:.2f}")
    with col2:
        st.metric("Total Saved Ever", f"€{total_saved:.2f}")
    with col3:
        st.metric("Best Month", f"{best_month['month']}")
    with col4:
        st.metric("Avg Savings Rate", f"{avg_savings_rate:.1f}%")

    st.divider()


    st.subheader("All Income Entries")

    csv = income_df.to_csv(index=False).encode("utf-8")
    st.download_button("Export to CSV", data=csv,
                       file_name="income.csv", mime="text/csv")

    st.dataframe(
        income_df[["date", "person", "source", "amount", "description"]].rename(
            columns={"date": "Date", "person": "Person", "source": "Source",
                     "amount": "Amount (€)", "description": "Description"}),
        use_container_width=True)

#By person
with tab2:
    st.subheader("Income by Person")

    if income_df.empty:
        st.warning("No data yet.")
        st.stop()

    persons = income_df["person"].unique()

    #yobs
    if not jobs_df.empty:
        st.subheader("Job Profiles")
        cols = st.columns(len(jobs_df))
        for col, (_, job) in zip(cols, jobs_df.iterrows()):
            with col:
                start = job["start_date"]
                if start:
                    try:
                        start_dt = datetime.strptime(start, "%Y-%m-%d")
                        months_worked = (
                            datetime.now() - start_dt).days // 30
                        years = months_worked // 12
                        months = months_worked % 12
                        duration = f"{years}y {months}m" if years > 0 else f"{months}m"
                    except:
                        duration = "N/A"
                else:
                    duration = "N/A"

                st.markdown(f"""
                <div style="
                    background-color: #1e1e2e;
                    border: 1px solid #333;
                    border-radius: 12px;
                    padding: 20px;
                ">
                    <h3 style="margin: 0; color: #00CC96;">{job['person']}</h3>
                    <p style="margin: 5px 0; font-size: 18px;">
                        <b>{job['employer'] or 'N/A'}</b>
                    </p>
                    <p style="color: #999; margin: 3px 0;">
                        {job['job_title'] or 'N/A'}
                    </p>
                    <p style="color: #999; margin: 3px 0;">
                        {job['contract_type'] or 'N/A'}
                    </p>
                    <hr style="border-color: #333;">
                    <p style="margin: 3px 0;">
                        Started: <b>{job['start_date'] or 'N/A'}</b>
                    </p>
                    <p style="margin: 3px 0;">
                        Duration: <b>{duration}</b>
                    </p>
                    <p style="margin: 3px 0;">
                        Net: <b>€{job['salary_net'] or 0:.2f}/month</b>
                    </p>
                    <p style="margin: 3px 0;">
                        Hours: <b>{job['hours_per_week'] or 0}h/week</b>
                    </p>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

    #per person metrics
    cols = st.columns(len(persons))
    for col, person in zip(cols, persons):
        person_data = income_df[income_df["person"] == person]
        person_this_month = person_data[
            person_data["date"].dt.strftime("%Y-%m") == this_month]
        with col:
            total = person_data["amount"].sum()
            this_m = person_this_month["amount"].sum()
            avg = person_data.groupby(
                person_data["date"].dt.strftime("%Y-%m"))["amount"].sum().mean()
            st.markdown(f"### {person}")
            st.metric("This Month", f"€{this_m:.2f}")
            st.metric("All Time Total", f"€{total:.2f}")
            st.metric("Monthly Average", f"€{avg:.2f}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        person_totals = income_df.groupby("person")["amount"].sum().reset_index()
        fig = px.pie(person_totals, values="amount", names="person",
                     title="Total Income Split by Person",
                     color_discrete_sequence=["#00CC96", "#AB63FA", "#FFD700"])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        income_df["month"] = income_df["date"].dt.strftime("%Y-%m")
        monthly_by_person = income_df.groupby(
            ["month", "person"])["amount"].sum().reset_index()
        fig = px.bar(monthly_by_person, x="month", y="amount", color="person",
                     title="Monthly Income by Person",
                     barmode="group",
                     color_discrete_sequence=["#00CC96", "#AB63FA", "#FFD700"])
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.area(monthly_by_person, x="month", y="amount", color="person",
                      title="Income Contribution Over Time",
                      color_discrete_sequence=["#00CC96", "#AB63FA", "#FFD700"])
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        source_totals = income_df.groupby("source")["amount"].sum().reset_index()
        fig = px.pie(source_totals, values="amount", names="source",
                     title="Income by Source",
                     color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    #payslips
    st.subheader("📄 Payslips")

    with st.expander("Upload Payslip"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            ps_person = st.selectbox("Person", people_list, key="ps_person")
        with col2:
            ps_month = st.text_input("Month (YYYY-MM)",
                                     value=today.strftime("%Y-%m"))
        with col3:
            ps_amount = st.number_input("Net Amount (€)", min_value=0.0,
                                        step=0.01, key="ps_amt")
        with col4:
            ps_notes = st.text_input("Notes", key="ps_notes")

        ps_file = st.file_uploader("Upload Payslip",
                                   type=["pdf", "png", "jpg", "jpeg"],
                                   key="ps_file")

        if st.button("💾 Save Payslip", type="primary"):
            if ps_file:
                os.makedirs("payslips", exist_ok=True)
                file_path = os.path.join(
                    "payslips", f"{ps_person}_{ps_month}_{ps_file.name}")
                with open(file_path, "wb") as f:
                    f.write(ps_file.getbuffer())
                conn = create_connection()
                conn.execute("""
                    INSERT INTO payslips
                    (person, month, file_path, amount, notes, uploaded_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (ps_person, ps_month, file_path, ps_amount,
                      ps_notes, str(date.today())))
                conn.commit()
                conn.close()
                st.success("Payslip saved!")
                st.rerun()
            else:
                st.warning("Please upload a file")

    if not payslips_df.empty:
        filter_person = st.selectbox(
            "Filter by Person",
            ["All"] + people_list,
            key="filter_ps"
        )

        filtered_ps = payslips_df if filter_person == "All" else \
            payslips_df[payslips_df["person"] == filter_person]

        for _, row in filtered_ps.iterrows():
            with st.expander(
                    f"{row['person']} — {row['month']} | €{row['amount'] or 0:.2f}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    if os.path.exists(row["file_path"]):
                        if row["file_path"].endswith(".pdf"):
                            with open(row["file_path"], "rb") as f:
                                b64 = base64.b64encode(f.read()).decode()
                            st.markdown(
                                f'<iframe src="data:application/pdf;base64,{b64}"'
                                f' width="100%" height="500px"></iframe>',
                                unsafe_allow_html=True)
                        else:
                            st.image(row["file_path"])
                    else:
                        st.warning("File not found")

                with col2:
                    st.write(f"**Person:** {row['person']}")
                    st.write(f"**Month:** {row['month']}")
                    st.write(f"**Amount:** €{row['amount'] or 0:.2f}")
                    st.write(f"**Notes:** {row['notes'] or '-'}")
                    st.write(f"**Uploaded:** {row['uploaded_date']}")

                    if os.path.exists(row["file_path"]):
                        with open(row["file_path"], "rb") as f:
                            st.download_button(
                                "⬇️ Download",
                                data=f,
                                file_name=os.path.basename(row["file_path"]),
                                key=f"dl_{row['id']}"
                            )
    else:
        st.info("No payslips uploaded yet.")

#Trends
with tab3:
    st.subheader("Income Trends")

    if income_df.empty:
        st.warning("No data yet.")
        st.stop()

    income_sorted = income_df.sort_values("date").copy()
    income_sorted["month"] = income_sorted["date"].dt.strftime("%Y-%m")
    monthly_totals = income_sorted.groupby("month")["amount"].sum().reset_index()
    monthly_totals.columns = ["month", "total"]
    monthly_totals["rolling_avg"] = monthly_totals["total"].rolling(3).mean()

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_totals["month"], y=monthly_totals["total"],
            name="Monthly Income", marker_color="#00CC96", opacity=0.7))
        fig.add_trace(go.Scatter(
            x=monthly_totals["month"], y=monthly_totals["rolling_avg"],
            name="3 Month Average", mode="lines",
            line=dict(color="#FFD700", width=3)))
        fig.update_layout(title="Income with Rolling Average",
                          xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        half = len(monthly_totals) // 2
        first_avg = monthly_totals.iloc[:half]["total"].mean()
        second_avg = monthly_totals.iloc[half:]["total"].mean()
        trend_pct = ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0

        color = "#00CC96" if trend_pct >= 0 else "#EF553B"
        direction = "Growing" if trend_pct >= 0 else "Declining"

        st.markdown(f"""
        <div style="
            background-color: {color}22;
            border: 3px solid {color};
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            margin-top: 20px;
        ">
            <p style="font-size: 16px; margin: 0;">Income Trend</p>
            <h1 style="color: {color}; font-size: 60px; margin: 10px 0;">
                {"↑" if trend_pct >= 0 else "↓"} {abs(trend_pct):.1f}%
            </h1>
            <h3 style="color: {color};">{direction}</h3>
            <p style="color: #999; font-size: 13px;">
                First half avg: €{first_avg:.2f} vs Recent avg: €{second_avg:.2f}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.subheader("Projections")

    avg_monthly = monthly_totals["total"].mean()
    projected_annual = avg_monthly * 12
    avg_exp_monthly = expenses_df.groupby(
        expenses_df["date"].dt.strftime("%Y-%m"))[
        "amount"].sum().mean() if not expenses_df.empty else 0
    projected_savings = (avg_monthly - avg_exp_monthly) * 12

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Avg Monthly Income", f"€{avg_monthly:.2f}")
    with col2:
        st.metric("Projected Annual Income", f"€{projected_annual:.2f}")
    with col3:
        st.metric("Projected Annual Savings", f"€{projected_savings:.2f}")

#SAVINGS
with tab4:
    st.subheader("Savings Tracker")

    if income_df.empty:
        st.warning("No data yet.")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        savings_goal = st.number_input(
            "Monthly Savings Goal (€)", min_value=0.0, value=500.0, step=50.0)

    st.divider()

    monthly_inc2 = income_df.copy()
    monthly_inc2["month"] = monthly_inc2["date"].dt.strftime("%Y-%m")
    inc_by_month = monthly_inc2.groupby("month")["amount"].sum().reset_index()
    inc_by_month.columns = ["month", "income"]

    if not expenses_df.empty:
        exp_by_month = expenses_df.copy()
        exp_by_month["month"] = exp_by_month["date"].dt.strftime("%Y-%m")
        exp_grouped = exp_by_month.groupby("month")["amount"].sum().reset_index()
        exp_grouped.columns = ["month", "expenses"]
        savings_data = inc_by_month.merge(
            exp_grouped, on="month", how="outer").fillna(0)
    else:
        savings_data = inc_by_month.copy()
        savings_data["expenses"] = 0

    savings_data["saved"] = savings_data["income"] - savings_data["expenses"]
    savings_data["cumulative"] = savings_data["saved"].cumsum()
    savings_data["goal_met"] = savings_data["saved"] >= savings_goal

    this_month_saved = savings_data[
        savings_data["month"] == this_month]["saved"].sum()
    goal_pct = (this_month_saved / savings_goal * 100) if savings_goal > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Saved This Month", f"€{this_month_saved:.2f}")
    with col2:
        st.metric("Monthly Goal", f"€{savings_goal:.2f}")
    with col3:
        st.metric("Goal Progress", f"{goal_pct:.1f}%")

    if goal_pct >= 100:
        st.success(f"Goal reached! Saved €{this_month_saved:.2f} this month")
    elif goal_pct >= 75:
        st.info(f"Almost there — {100 - goal_pct:.1f}% left")
    elif goal_pct >= 50:
        st.warning("Halfway there — keep going")
    else:
        st.error("Behind on savings goal this month")

    st.progress(min(goal_pct / 100, 1.0))
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        colors = ["#00CC96" if g else "#EF553B" for g in savings_data["goal_met"]]
        fig = go.Figure(go.Bar(
            x=savings_data["month"], y=savings_data["saved"],
            marker_color=colors))
        fig.add_hline(y=savings_goal, line_dash="dash",
                      annotation_text=f"Goal €{savings_goal:.0f}",
                      line_color="#FFD700")
        fig.update_layout(title="Monthly Savings vs Goal",
                          xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.area(savings_data, x="month", y="cumulative",
                      title="Cumulative Savings Over Time",
                      color_discrete_sequence=["#00CC96"])
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("House Down Payment Calculator")

    col1, col2 = st.columns(2)

    with col1:
        house_price = st.number_input(
            "Target House Price (€)", min_value=0.0,
            value=250000.0, step=10000.0)
        down_payment_pct = st.slider(
            "Down Payment %", min_value=10, max_value=40, value=20)

    with col2:
        down_payment = house_price * (down_payment_pct / 100)
        buying_costs = house_price * 0.115
        total_needed = down_payment + buying_costs
        current_savings = savings_data["cumulative"].iloc[-1] \
            if not savings_data.empty else 0
        remaining = max(total_needed - current_savings, 0)
        months_needed = remaining / savings_goal if savings_goal > 0 else 0
        years_needed = months_needed / 12

        st.metric("Down Payment Needed", f"€{down_payment:.2f}")
        st.metric("Buying Costs NRW ~11.5%", f"€{buying_costs:.2f}")
        st.metric("Total Needed", f"€{total_needed:.2f}")
        st.metric("Current Savings", f"€{current_savings:.2f}")

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Still Needed", f"€{remaining:.2f}")
    with col2:
        st.metric("Months to Goal", f"{months_needed:.0f}")
    with col3:
        st.metric("Years to Goal", f"{years_needed:.1f}")

    target_date = pd.Timestamp.now() + pd.DateOffset(months=int(months_needed))
    st.info(
        f"At your current savings rate of €{savings_goal:.0f}/month "
        f"you could afford this house by **{target_date.strftime('%B %Y')}**")

#recurring
with tab5:
    st.subheader("🔄 Recurring Income")
    st.caption("Set up income that repeats every month — log it all at once")

    #add
    with st.expander("➕ Add Recurring Income"):
        with st.form("recurring_form"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                rec_person = st.selectbox("Person", people_list, key="rec_person")
            with col2:
                rec_source = st.selectbox("Source", sources_list, key="rec_source")
            with col3:
                rec_amount = st.number_input(
                    "Monthly Amount (€)", min_value=0.0, step=0.01)
            with col4:
                rec_desc = st.text_input("Description", key="rec_desc")

            if st.form_submit_button("💾 Save Recurring Income", type="primary"):
                if rec_amount > 0:
                    conn = create_connection()
                    conn.execute("""
                        INSERT INTO recurring_income
                        (person, source, amount, description, active)
                        VALUES (?, ?, ?, ?, 1)
                    """, (rec_person, rec_source, rec_amount, rec_desc))
                    conn.commit()
                    conn.close()
                    st.success("Recurring income saved!")
                    st.rerun()

    st.divider()

    if not recurring_df.empty:
        st.subheader("Active Recurring Income")

        total_recurring = recurring_df["amount"].sum()
        st.metric("Total Monthly Recurring", f"€{total_recurring:.2f}")
        st.divider()

        for _, row in recurring_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
            with col1:
                st.write(f"**{row['person']}**")
            with col2:
                st.write(row["source"])
            with col3:
                st.write(f"€{row['amount']:.2f}/month")
            with col4:
                st.write(row["description"] or "—")
            with col5:
                if st.button("🗑️", key=f"del_rec_{row['id']}"):
                    conn = create_connection()
                    conn.execute(
                        "UPDATE recurring_income SET active=0 WHERE id=?",
                        (row["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()

        st.divider()

        st.subheader("Log Recurring Income")
        st.caption("Click to add all recurring entries for a specific month")

        log_month = st.text_input(
            "Month to log (YYYY-MM)", value=today.strftime("%Y-%m"))

        if st.button("📥 Log All Recurring for This Month", type="primary"):
            conn = create_connection()
            count = 0
            for _, row in recurring_df.iterrows():
                conn.execute("""
                    INSERT INTO income (date, person, source, amount, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (f"{log_month}-01", row["person"], row["source"],
                      row["amount"], row["description"]))
                count += 1
            conn.commit()
            conn.close()
            st.success(f"Logged {count} recurring income entries for {log_month}!")
            st.rerun()
    else:
        st.info("No recurring income set up yet. Add one above.")

#Manage
with tab6:
    st.subheader("⚙️ Manage People & Sources")

    col1, col2 = st.columns(2)

    #people
    with col1:
        st.markdown("### 👤 People")

        if people_list:
            cols = st.columns(2)
            for i, person in enumerate(people_list):
                with cols[i % 2]:
                    st.markdown(f"""
                    <div style="
                        background-color: #1e1e2e;
                        border: 1px solid #333;
                        border-radius: 10px;
                        padding: 12px 16px;
                        margin-bottom: 10px;
                        display: flex;
                        align-items: center;
                    ">
                        <span style="font-size: 16px;">👤 <b>{person}</b></span>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("🗑️ Remove", key=f"del_person_{person}"):
                        conn = create_connection()
                        conn.execute(
                            "DELETE FROM people WHERE name=?", (person,))
                        conn.commit()
                        conn.close()
                        st.rerun()
        else:
            st.info("No people added yet.")

        st.divider()
        new_person = st.text_input("Add New Person", key="new_person_mgmt")
        if st.button("➕ Add Person", key="add_person_btn"):
            if new_person.strip():
                conn = create_connection()
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO people (name) VALUES (?)",
                        (new_person.strip(),))
                    conn.commit()
                    st.success(f"Added {new_person}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    conn.close()

    #sources
    with col2:
        st.markdown("### 💼 Income Sources")

        if sources_list:
            cols = st.columns(2)
            for i, source in enumerate(sources_list):
                with cols[i % 2]:
                    st.markdown(f"""
                    <div style="
                        background-color: #1e1e2e;
                        border: 1px solid #333;
                        border-radius: 10px;
                        padding: 12px 16px;
                        margin-bottom: 10px;
                    ">
                        <span style="font-size: 16px;">💼 <b>{source}</b></span>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("🗑️ Remove", key=f"del_source_{source}"):
                        conn = create_connection()
                        conn.execute(
                            "DELETE FROM income_sources WHERE name=?", (source,))
                        conn.commit()
                        conn.close()
                        st.rerun()
        else:
            st.info("No sources added yet.")

        st.divider()
        new_source = st.text_input("Add New Source", key="new_source_mgmt")
        if st.button("➕ Add Source", key="add_source_btn"):
            if new_source.strip():
                conn = create_connection()
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO income_sources (name) VALUES (?)",
                        (new_source.strip(),))
                    conn.commit()
                    st.success(f"Added {new_source}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    conn.close()

    st.divider()

    #jobs
    st.subheader("💼 Job Profiles")
    st.caption("Track employment details per person")

    selected_person = st.selectbox(
        "Select Person to Edit Job Profile",
        people_list if people_list else ["Add a person above"])

    if selected_person and people_list:
        existing = jobs_df[jobs_df["person"] == selected_person].iloc[0] \
            if not jobs_df.empty and selected_person in jobs_df["person"].values \
            else None

        with st.form("job_profile_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                employer = st.text_input(
                    "Employer",
                    value=existing["employer"] if existing is not None
                    and existing["employer"] else "")
                job_title = st.text_input(
                    "Job Title",
                    value=existing["job_title"] if existing is not None
                    and existing["job_title"] else "")
                contract_type = st.selectbox(
                    "Contract Type",
                    ["Full Time", "Part Time", "Werkstudent",
                     "Ausbildung", "Minijob", "Freelance", "Other"],
                    index=0)

            with col2:
                start_date = st.text_input(
                    "Start Date (YYYY-MM-DD)",
                    value=existing["start_date"] if existing is not None
                    and existing["start_date"] else "")
                salary_net = st.number_input(
                    "Net Salary (€/month)",
                    value=float(existing["salary_net"])
                    if existing is not None and existing["salary_net"] else 0.0,
                    min_value=0.0, step=0.01)
                salary_gross = st.number_input(
                    "Gross Salary (€/month)",
                    value=float(existing["salary_gross"])
                    if existing is not None and existing["salary_gross"] else 0.0,
                    min_value=0.0, step=0.01)

            with col3:
                hours_per_week = st.number_input(
                    "Hours per Week",
                    value=float(existing["hours_per_week"])
                    if existing is not None and existing["hours_per_week"] else 0.0,
                    min_value=0.0, step=0.5)
                notes = st.text_area(
                    "Notes",
                    value=existing["notes"] if existing is not None
                    and existing["notes"] else "")

            if st.form_submit_button("💾 Save Job Profile", type="primary"):
                conn = create_connection()
                if existing is not None:
                    conn.execute("""
                        UPDATE job_profiles SET
                        employer=?, job_title=?, contract_type=?,
                        start_date=?, salary_net=?, salary_gross=?,
                        hours_per_week=?, notes=?
                        WHERE person=?
                    """, (employer, job_title, contract_type, start_date,
                          salary_net, salary_gross, hours_per_week,
                          notes, selected_person))
                else:
                    conn.execute("""
                        INSERT INTO job_profiles
                        (person, employer, job_title, contract_type,
                        start_date, salary_net, salary_gross,
                        hours_per_week, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (selected_person, employer, job_title, contract_type,
                          start_date, salary_net, salary_gross,
                          hours_per_week, notes))
                conn.commit()
                conn.close()
                st.success(f"Job profile saved for {selected_person}!")
                st.rerun()