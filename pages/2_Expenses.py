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

#load data
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
    jobs_df = pd.read_sql_query(
        "SELECT * FROM job_profiles ORDER BY person, start_date DESC", conn)
except:
    jobs_df = pd.DataFrame()

try:
    salary_history_df = pd.read_sql_query(
        "SELECT * FROM salary_history ORDER BY date DESC", conn)
except:
    salary_history_df = pd.DataFrame()

conn.close()

if not income_df.empty:
    income_df["date"] = pd.to_datetime(income_df["date"])
if not expenses_df.empty:
    expenses_df["date"] = pd.to_datetime(expenses_df["date"])

today = pd.Timestamp.now()
this_month = today.strftime("%Y-%m")
last_month = (today - timedelta(days=30)).strftime("%Y-%m")

#tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview",
    "💼 Jobs",
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

    #metrics
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

    #charts
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

#Jobs
with tab2:
    st.subheader("💼 Jobs")

    #person filter
    person_filter = st.selectbox(
        "Filter by Person",
        ["All"] + people_list,
        key="jobs_person_filter"
    )

    filtered_jobs = jobs_df if person_filter == "All" else \
        jobs_df[jobs_df["person"] == person_filter] if not jobs_df.empty else pd.DataFrame()

    st.divider()

    if jobs_df.empty:
        st.info("No jobs added yet. Use the Manage tab to add jobs.")
    else:
        #active jobs
        active_jobs = filtered_jobs[filtered_jobs["status"] == "active"] \
            if not filtered_jobs.empty else pd.DataFrame()
        past_jobs = filtered_jobs[filtered_jobs["status"] != "active"] \
            if not filtered_jobs.empty else pd.DataFrame()

        if not active_jobs.empty:
            st.subheader("Current Jobs")

            cols = st.columns(min(len(active_jobs), 3))
            for col, (_, job) in zip(cols, active_jobs.iterrows()):
                with col:
                    #duration
                    if job["start_date"]:
                        try:
                            start_dt = datetime.strptime(job["start_date"], "%Y-%m-%d")
                            days = (datetime.now() - start_dt).days
                            years = days // 365
                            months = (days % 365) // 30
                            duration = f"{years}y {months}m" if years > 0 else f"{months}m"
                        except:
                            duration = "N/A"
                    else:
                        duration = "N/A"

                    st.markdown(f"""
                    <div style="
                        background-color: #1a2e1a;
                        border: 1px solid #00CC96;
                        border-radius: 14px;
                        padding: 20px;
                        margin-bottom: 15px;
                    ">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <h3 style="margin:0; color:#00CC96;">{job['person']}</h3>
                            <span style="background:#00CC9622; color:#00CC96;
                                padding:4px 12px; border-radius:20px; font-size:12px;
                                border:1px solid #00CC96;">● Active</span>
                        </div>
                        <p style="font-size:20px; margin:0 0 4px 0;"><b>{job['employer'] or 'N/A'}</b></p>
                        <p style="color:#aaa; margin:0 0 12px 0;">
                            {job['job_title'] or 'N/A'} · {job['contract_type'] or 'N/A'}
                        </p>
                        <hr style="border-color:#2a3a2a; margin:10px 0;">
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                            <div>
                                <p style="color:#888; font-size:11px; margin:0;">STARTED</p>
                                <p style="margin:0;"><b>{job['start_date'] or 'N/A'}</b></p>
                            </div>
                            <div>
                                <p style="color:#888; font-size:11px; margin:0;">DURATION</p>
                                <p style="margin:0;"><b>{duration}</b></p>
                            </div>
                            <div>
                                <p style="color:#888; font-size:11px; margin:0;">NET SALARY</p>
                                <p style="margin:0; color:#00CC96;"><b>€{job['salary_net'] or 0:.2f}/mo</b></p>
                            </div>
                            <div>
                                <p style="color:#888; font-size:11px; margin:0;">GROSS SALARY</p>
                                <p style="margin:0;"><b>€{job['salary_gross'] or 0:.2f}/mo</b></p>
                            </div>
                            <div>
                                <p style="color:#888; font-size:11px; margin:0;">HOURS/WEEK</p>
                                <p style="margin:0;"><b>{job['hours_per_week'] or 0}h</b></p>
                            </div>
                            <div>
                                <p style="color:#888; font-size:11px; margin:0;">HOLIDAY DAYS</p>
                                <p style="margin:0;"><b>{job['holiday_days'] or 'N/A'}</b></p>
                            </div>
                            <div>
                                <p style="color:#888; font-size:11px; margin:0;">NOTICE PERIOD</p>
                                <p style="margin:0;"><b>{job['notice_period'] or 'N/A'}</b></p>
                            </div>
                            <div>
                                <p style="color:#888; font-size:11px; margin:0;">HOURLY RATE</p>
                                <p style="margin:0;"><b>€{(job['salary_gross'] or 0) / ((job['hours_per_week'] or 1) * 4.33):.2f}/h</b></p>
                            </div>
                        </div>
                        {f'<hr style="border-color:#2a3a2a; margin:10px 0;"><p style="color:#888; font-size:12px; margin:0;">{job["notes"]}</p>' if job["notes"] else ""}
                    </div>
                    """, unsafe_allow_html=True)

        st.divider()

        #timeline
        st.subheader("Job Timeline")

        if not filtered_jobs.empty:
            for person in filtered_jobs["person"].unique():
                person_jobs = filtered_jobs[filtered_jobs["person"] == person].copy()
                person_jobs = person_jobs.sort_values("start_date")

                st.markdown(f"**{person}**")

                for _, job in person_jobs.iterrows():
                    is_active = job["status"] == "active"
                    border_color = "#00CC96" if is_active else "#555"
                    bg_color = "#1a2e1a" if is_active else "#1e1e1e"
                    status_text = "Active" if is_active else "Ended"
                    status_color = "#00CC96" if is_active else "#888"
                    end_display = job["end_date"] if job["end_date"] else "Present"

                    #duration
                    if job["start_date"]:
                        try:
                            start_dt = datetime.strptime(job["start_date"], "%Y-%m-%d")
                            end_dt = datetime.strptime(
                                job["end_date"], "%Y-%m-%d") if job["end_date"] else datetime.now()
                            days = (end_dt - start_dt).days
                            years = days // 365
                            months = (days % 365) // 30
                            duration = f"{years}y {months}m" if years > 0 else f"{months}m"
                        except:
                            duration = "N/A"
                    else:
                        duration = "N/A"

                    st.markdown(f"""
                    <div style="
                        display: flex;
                        align-items: stretch;
                        margin-bottom: 8px;
                    ">
                        <div style="
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            margin-right: 15px;
                        ">
                            <div style="
                                width: 14px; height: 14px;
                                border-radius: 50%;
                                background: {border_color};
                                margin-top: 20px;
                                flex-shrink: 0;
                            "></div>
                            <div style="
                                width: 2px;
                                background: #333;
                                flex: 1;
                                margin-top: 4px;
                            "></div>
                        </div>
                        <div style="
                            background-color: {bg_color};
                            border: 1px solid {border_color};
                            border-radius: 10px;
                            padding: 14px 18px;
                            flex: 1;
                            margin-bottom: 4px;
                        ">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <b style="font-size:16px;">{job['employer'] or 'N/A'}</b>
                                    <span style="color:#888; margin-left:8px;">
                                        {job['job_title'] or ''} · {job['contract_type'] or ''}
                                    </span>
                                </div>
                                <span style="color:{status_color}; font-size:12px;">
                                    ● {status_text}
                                </span>
                            </div>
                            <div style="color:#888; font-size:13px; margin-top:6px;">
                                {job['start_date'] or 'N/A'} → {end_display}
                                · <b>{duration}</b>
                                · Net: <b style="color:{border_color};">€{job['salary_net'] or 0:.2f}/mo</b>
                                {f'· {job["hours_per_week"]}h/week' if job["hours_per_week"] else ''}
                                {f'· {job["holiday_days"]} days holiday' if job["holiday_days"] else ''}
                                {f'· Notice: {job["notice_period"]}' if job["notice_period"] else ''}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.write("")

        st.divider()

        #analytics
        st.subheader("Analytics")

        col1, col2 = st.columns(2)

        with col1:
            #salary progression
            if not filtered_jobs.empty:
                salary_data = filtered_jobs[
                    filtered_jobs["start_date"].notna()].copy()
                salary_data = salary_data.sort_values("start_date")

                if not salary_data.empty:
                    fig = go.Figure()
                    for person in salary_data["person"].unique():
                        person_data = salary_data[salary_data["person"] == person]
                        fig.add_trace(go.Scatter(
                            x=person_data["start_date"],
                            y=person_data["salary_net"],
                            name=f"{person} Net",
                            mode="lines+markers",
                            marker=dict(size=10),
                            line=dict(width=3)
                        ))
                    fig.update_layout(
                        title="Salary Progression Over Time",
                        xaxis_title="Job Start Date",
                        yaxis_title="Net Salary (€/month)",
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig, use_container_width=True)

        with col2:
            #job comparison
            if not filtered_jobs.empty and len(filtered_jobs) >= 2:
                st.markdown("**Compare Jobs**")
                job_labels = [
                    f"{row['person']} — {row['employer']}"
                    for _, row in filtered_jobs.iterrows()
                ]
                selected_jobs = st.multiselect(
                    "Select jobs to compare",
                    job_labels,
                    default=job_labels[:2],
                    key="compare_jobs"
                )

                if len(selected_jobs) >= 2:
                    compare_data = []
                    for label in selected_jobs:
                        idx = job_labels.index(label)
                        job = filtered_jobs.iloc[idx]
                        hourly = (job["salary_gross"] or 0) / \
                                 ((job["hours_per_week"] or 1) * 4.33)
                        compare_data.append({
                            "Job": f"{job['employer']}",
                            "Person": job["person"],
                            "Net/month": job["salary_net"] or 0,
                            "Gross/month": job["salary_gross"] or 0,
                            "Hours/week": job["hours_per_week"] or 0,
                            "Hourly Rate": round(hourly, 2),
                            "Holiday Days": job["holiday_days"] or 0,
                            "Notice Period": job["notice_period"] or "N/A"
                        })

                    compare_df = pd.DataFrame(compare_data)

                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        name="Net Salary",
                        x=compare_df["Job"],
                        y=compare_df["Net/month"],
                        marker_color="#00CC96"
                    ))
                    fig.add_trace(go.Bar(
                        name="Gross Salary",
                        x=compare_df["Job"],
                        y=compare_df["Gross/month"],
                        marker_color="#AB63FA"
                    ))
                    fig.update_layout(
                        barmode="group",
                        title="Salary Comparison"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.dataframe(
                        compare_df.set_index("Job"),
                        use_container_width=True
                    )
            else:
                st.info("Add at least 2 jobs to compare them.")

        st.divider()

        #past jobs
        if not past_jobs.empty:
            st.subheader("Past Jobs")
            for _, job in past_jobs.iterrows():
                if job["start_date"] and job["end_date"]:
                    try:
                        start_dt = datetime.strptime(job["start_date"], "%Y-%m-%d")
                        end_dt = datetime.strptime(job["end_date"], "%Y-%m-%d")
                        days = (end_dt - start_dt).days
                        years = days // 365
                        months = (days % 365) // 30
                        duration = f"{years}y {months}m" if years > 0 else f"{months}m"
                    except:
                        duration = "N/A"
                else:
                    duration = "N/A"

                st.markdown(f"""
                <div style="
                    background-color: #1a1a1a;
                    border: 1px solid #444;
                    border-radius: 10px;
                    padding: 15px 20px;
                    margin-bottom: 8px;
                    opacity: 0.75;
                ">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <b style="font-size:15px;">{job['person']}</b>
                            <span style="color:#888; margin:0 8px;">at</span>
                            <b style="font-size:15px;">{job['employer'] or 'N/A'}</b>
                            <span style="color:#666; margin-left:10px; font-size:13px;">
                                {job['job_title'] or ''} · {job['contract_type'] or ''}
                            </span>
                        </div>
                        <div style="text-align:right; color:#888; font-size:13px;">
                            {job['start_date'] or 'N/A'} → {job['end_date'] or 'N/A'}
                            · <b>{duration}</b><br>
                            Net: €{job['salary_net'] or 0:.2f}/mo
                            {f'· {job["hours_per_week"]}h/week' if job["hours_per_week"] else ''}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        #payslips
        st.divider()
        st.subheader("📄 Payslips")

        with st.expander("Upload Payslip"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                ps_person = st.selectbox("Person", people_list, key="ps_person")
            with col2:
                ps_month = st.text_input(
                    "Month (YYYY-MM)", value=today.strftime("%Y-%m"))
            with col3:
                ps_amount = st.number_input(
                    "Net Amount (€)", min_value=0.0, step=0.01, key="ps_amt")
            with col4:
                ps_notes = st.text_input("Notes", key="ps_notes")

            ps_file = st.file_uploader(
                "Upload Payslip", type=["pdf", "png", "jpg", "jpeg"], key="ps_file")

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
            ps_filter = st.selectbox(
                "Filter by Person", ["All"] + people_list, key="filter_ps")
            filtered_ps = payslips_df if ps_filter == "All" else \
                payslips_df[payslips_df["person"] == ps_filter]

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
                                    "⬇️ Download", data=f,
                                    file_name=os.path.basename(row["file_path"]),
                                    key=f"dl_{row['id']}")
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

#Savings
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

#Recurring
with tab5:
    st.subheader("🔄 Recurring Income")
    st.caption("Set up income that repeats every month")

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

            if st.form_submit_button("💾 Save", type="primary"):
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
        st.metric("Total Monthly Recurring", f"€{recurring_df['amount'].sum():.2f}")
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
            st.success(f"Logged {count} entries for {log_month}!")
            st.rerun()
    else:
        st.info("No recurring income set up yet.")

#Manage
with tab6:
    st.subheader("⚙️ Manage People, Sources & Jobs")

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
                    ">
                        <span style="font-size: 16px;">👤 <b>{person}</b></span>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("🗑️ Remove", key=f"del_person_{person}"):
                        conn = create_connection()
                        conn.execute("DELETE FROM people WHERE name=?", (person,))
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
    st.subheader("💼 Job Management")

    job_action = st.radio("Action", ["Add New Job", "Edit Job", "End a Job"], horizontal=True)

    if job_action == "Add New Job":
        with st.form("add_job_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                job_person = st.selectbox(
                    "Person", people_list if people_list else ["Add a person above"])
                employer = st.text_input("Employer")
                job_title = st.text_input("Job Title")
                contract_type = st.selectbox(
                    "Contract Type",
                    ["Full Time", "Part Time", "Werkstudent",
                     "Ausbildung", "Minijob", "Freelance", "Other"])

            with col2:
                start_date = st.text_input("Start Date (YYYY-MM-DD)")
                salary_net = st.number_input(
                    "Net Salary (€/month)", min_value=0.0, step=0.01)
                salary_gross = st.number_input(
                    "Gross Salary (€/month)", min_value=0.0, step=0.01)
                hours_per_week = st.number_input(
                    "Hours per Week", min_value=0.0, step=0.5)

            with col3:
                notice_period = st.text_input(
                    "Notice Period (e.g. 4 weeks, 3 months)")
                holiday_days = st.number_input(
                    "Holiday Days per Year", min_value=0, step=1)
                notes = st.text_area("Notes")
                auto_source = st.checkbox(
                    "Auto-add employer as income source", value=True)
                auto_recurring = st.checkbox(
                    "Auto-create recurring income entry", value=True)

            if st.form_submit_button("💾 Add Job", type="primary"):
                if employer and job_person:
                    conn = create_connection()
                    conn.execute("""
                        INSERT INTO job_profiles
                        (person, employer, job_title, contract_type, start_date,
                        end_date, status, salary_net, salary_gross,
                        hours_per_week, notice_period, holiday_days, notes)
                        VALUES (?, ?, ?, ?, ?, NULL, 'active', ?, ?, ?, ?, ?, ?)
                    """, (job_person, employer, job_title, contract_type,
                          start_date, salary_net, salary_gross,
                          hours_per_week, notice_period, holiday_days, notes))

                    if auto_source and employer:
                        conn.execute(
                            "INSERT OR IGNORE INTO income_sources (name) VALUES (?)",
                            (employer,))

                    if auto_recurring and salary_net > 0:
                        conn.execute("""
                            INSERT INTO recurring_income
                            (person, source, amount, description, active)
                            VALUES (?, ?, ?, ?, 1)
                        """, (job_person, employer, salary_net,
                              f"Monthly salary — {employer}"))

                    conn.commit()
                    conn.close()
                    st.success(f"Job added for {job_person} at {employer}!")
                    st.rerun()
                else:
                    st.warning("Person and employer are required")

    elif job_action == "Edit Job":
        if not jobs_df.empty:
            job_labels = [
                f"{row['person']} — {row['employer']} ({row['status']})"
                for _, row in jobs_df.iterrows()
            ]
            selected_label = st.selectbox("Select Job", job_labels)
            selected_idx = job_labels.index(selected_label)
            job = jobs_df.iloc[selected_idx]

            with st.form("edit_job_form"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    employer = st.text_input("Employer", value=job["employer"] or "")
                    job_title = st.text_input("Job Title", value=job["job_title"] or "")
                    contract_type = st.selectbox(
                        "Contract Type",
                        ["Full Time", "Part Time", "Werkstudent",
                         "Ausbildung", "Minijob", "Freelance", "Other"],
                        index=["Full Time", "Part Time", "Werkstudent",
                               "Ausbildung", "Minijob", "Freelance",
                               "Other"].index(job["contract_type"])
                        if job["contract_type"] in ["Full Time", "Part Time",
                                                     "Werkstudent", "Ausbildung",
                                                     "Minijob", "Freelance", "Other"]
                        else 0)

                with col2:
                    start_date = st.text_input(
                        "Start Date", value=job["start_date"] or "")
                    salary_net = st.number_input(
                        "Net Salary (€/month)",
                        value=float(job["salary_net"] or 0), min_value=0.0, step=0.01)
                    salary_gross = st.number_input(
                        "Gross Salary (€/month)",
                        value=float(job["salary_gross"] or 0), min_value=0.0, step=0.01)
                    hours_per_week = st.number_input(
                        "Hours per Week",
                        value=float(job["hours_per_week"] or 0),
                        min_value=0.0, step=0.5)

                with col3:
                    notice_period = st.text_input(
                        "Notice Period", value=job["notice_period"] or "")
                    holiday_days = st.number_input(
                        "Holiday Days", value=int(job["holiday_days"] or 0),
                        min_value=0, step=1)
                    notes = st.text_area("Notes", value=job["notes"] or "")

                if st.form_submit_button("💾 Save Changes", type="primary"):
                    conn = create_connection()
                    conn.execute("""
                        UPDATE job_profiles SET
                        employer=?, job_title=?, contract_type=?, start_date=?,
                        salary_net=?, salary_gross=?, hours_per_week=?,
                        notice_period=?, holiday_days=?, notes=?
                        WHERE id=?
                    """, (employer, job_title, contract_type, start_date,
                          salary_net, salary_gross, hours_per_week,
                          notice_period, holiday_days, notes, job["id"]))
                    conn.commit()
                    conn.close()
                    st.success("Job updated!")
                    st.rerun()
        else:
            st.info("No jobs added yet.")

    else:
        #end a job
        if not jobs_df.empty:
            active_jobs = jobs_df[jobs_df["status"] == "active"]
            if not active_jobs.empty:
                job_labels = [
                    f"{row['person']} — {row['employer']} (since {row['start_date']})"
                    for _, row in active_jobs.iterrows()
                ]
                selected_label = st.selectbox("Select Job to End", job_labels)
                selected_idx = job_labels.index(selected_label)
                selected_job = active_jobs.iloc[selected_idx]

                end_date = st.text_input(
                    "End Date (YYYY-MM-DD)", value=today.strftime("%Y-%m-%d"))

                deactivate_recurring = st.checkbox(
                    "Also deactivate recurring income for this job", value=True)

                if st.button("🔴 End Job", type="primary"):
                    conn = create_connection()
                    conn.execute("""
                        UPDATE job_profiles SET status='inactive', end_date=?
                        WHERE id=?
                    """, (end_date, selected_job["id"]))

                    if deactivate_recurring:
                        conn.execute("""
                            UPDATE recurring_income SET active=0
                            WHERE person=? AND source=?
                        """, (selected_job["person"], selected_job["employer"]))

                    conn.commit()
                    conn.close()
                    st.success(
                        f"Job ended for {selected_job['person']} at "
                        f"{selected_job['employer']}")
                    st.rerun()
            else:
                st.info("No active jobs to end.")
        else:
            st.info("No jobs added yet.")

    st.divider()

    #all jobs table
    if not jobs_df.empty:
        st.subheader("All Jobs")
        st.dataframe(
            jobs_df[["person", "employer", "job_title", "contract_type",
                     "start_date", "end_date", "status", "salary_net",
                     "hours_per_week", "notice_period", "holiday_days"]].rename(
                columns={"person": "Person", "employer": "Employer",
                         "job_title": "Title", "contract_type": "Type",
                         "start_date": "Start", "end_date": "End",
                         "status": "Status", "salary_net": "Net (€)",
                         "hours_per_week": "Hrs/Week",
                         "notice_period": "Notice",
                         "holiday_days": "Holidays"}),
            use_container_width=True)