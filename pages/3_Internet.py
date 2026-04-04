import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from database import create_connection, create_tables

create_tables()

st.set_page_config(page_title="Internet", page_icon="🌐", layout="wide")
st.title("🌐 Internet Speed & Performance")
st.divider()

#Load data
conn = create_connection()
speed_df = pd.read_sql_query("SELECT * FROM internet_speed ORDER BY date", conn)
conn.close()

#Bufferbloat calculation
def calculate_bufferbloat(download, ping):
    if download == 0:
        return "F", "Cannot calculate — no download speed"
    ratio = ping / download
    if ratio < 0.5:
        return "A", "Excellent — minimal bufferbloat"
    elif ratio < 1.0:
        return "B", "Good — slight bufferbloat"
    elif ratio < 2.0:
        return "C", "Fair — noticeable bufferbloat"
    elif ratio < 4.0:
        return "D", "Poor — significant bufferbloat"
    else:
        return "F", "Failing — severe bufferbloat"

def grade_color(grade):
    colors = {
        "A": "#00CC96",
        "B": "#7FBA00",
        "C": "#FFD700",
        "D": "#FF6B35",
        "F": "#EF553B"
    }
    return colors.get(grade, "#999")

#Tabs
tab1, tab2, tab3 = st.tabs([
    " Overview",
    " Bufferbloat",
    " Trends"
])

#Overview
with tab1:

    st.subheader("Run Speed Test")
    st.caption("Runs a real time speedtest against the best available server using speedtest-cl")

    if st.button("Start Speed Test", type="primary"):
        with st.spinner("Running speed test... this takes 15-30 seconds"):
            try:
                import speedtest
                s = speedtest.Speedtest()
                s.get_best_server()
                download_speed = s.download() / 1_000_000
                upload_speed = s.upload() / 1_000_000
                ping_result = s.results.ping

                now = pd.Timestamp.now()
                hour = now.hour

                if 6 <= hour < 12:
                    time_of_day = "Morning"
                elif 12 <= hour < 17:
                    time_of_day = "Afternoon"
                elif 17 <= hour < 21:
                    time_of_day = "Evening"
                else:
                    time_of_day = "Night"

                conn = create_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO internet_speed (date, download, upload, ping, time_of_day)
                    VALUES (?, ?, ?, ?, ?)
                """, (now.strftime("%Y-%m-%d"),
                      round(download_speed, 2),
                      round(upload_speed, 2),
                      round(ping_result, 2),
                      time_of_day))
                conn.commit()
                conn.close()

                grade, description = calculate_bufferbloat(download_speed, ping_result)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Download", f"{download_speed:.1f} Mbps")
                with col2:
                    st.metric("Upload", f"{upload_speed:.1f} Mbps")
                with col3:
                    st.metric("Ping", f"{ping_result:.1f} ms")
                with col4:
                    st.metric("Bufferbloat Grade", grade)

                if grade in ["A", "B"]:
                    st.success(f"Grade {grade} — {description}")
                elif grade == "C":
                    st.warning(f"Grade {grade} — {description}")
                else:
                    st.error(f"Grade {grade} — {description}")

                st.success("Speed test saved!")
                st.rerun()

            except ImportError:
                st.error("speedtest-cli not installed. Run: pip install speedtest-cli")
            except Exception as e:
                st.error(f"Speed test failed: {e}")

    st.divider()

    if speed_df.empty:
        st.warning("No data. Run speed test")
        st.stop()

    st.subheader("Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    avg_download = speed_df["download"].mean()
    avg_upload = speed_df["upload"].mean()
    avg_ping = speed_df["ping"].mean()
    best_download = speed_df["download"].max()
    overall_grade, overall_desc = calculate_bufferbloat(avg_download, avg_ping)

    with col1:
        st.metric("Avg Download", f"{avg_download:.1f} Mbps")
    with col2:
        st.metric("Avg Upload", f"{avg_upload:.1f} Mbps")
    with col3:
        st.metric("Avg Ping", f"{avg_ping:.1f} ms")
    with col4:
        st.metric("Best Download", f"{best_download:.1f} Mbps")
    with col5:
        st.metric("Overall Bufferbloat", overall_grade)

    st.divider()

    st.subheader("Speed History")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(speed_df, x="date", y=["download", "upload"],
                      title="Download & Upload Speed (Mbps)",
                      markers=True,
                      color_discrete_sequence=["#00CC96", "#AB63FA"])
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(speed_df, x="date", y="ping",
                      title="Ping Over Time (ms)",
                      markers=True,
                      color_discrete_sequence=["#EF553B"])
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(speed_df, x="date", y="download",
                     title="Download Speed Per Test",
                     color="download",
                     color_continuous_scale="Viridis")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.scatter(speed_df, x="download", y="ping",
                         title="Download Speed vs Ping",
                         color="ping",
                         color_continuous_scale="RdYlGn_r",
                         size="download")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Raw Data")

    csv = speed_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Export to CSV",
        data=csv,
        file_name="internet_speed.csv",
        mime="text/csv"
    )

    st.dataframe(speed_df, use_container_width=True)

#Bufferbloat
with tab2:
    st.subheader("Bufferbloat Analysis")


    st.divider()

    st.subheader("Grade Scale")

    col1, col2, col3, col4, col5 = st.columns(5)

    grades = [
        ("A", "Excellent", "Minimal bufferbloat. Gaming and video calls are smooth."),
        ("B", "Good", "Slight bufferbloat. Most activities work well."),
        ("C", "Fair", "Noticeable bufferbloat. Gaming may suffer."),
        ("D", "Poor", "Significant bufferbloat. Expect lag and stuttering."),
        ("F", "Failing", "Severe bufferbloat. Connection is problematic.")
    ]

    for col, (grade, label, desc) in zip([col1, col2, col3, col4, col5], grades):
        with col:
            color = grade_color(grade)
            st.markdown(f"""
            <div style="
                background-color: {color}22;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 15px;
                text-align: center;
            ">
                <h1 style="color: {color}; margin: 0;">{grade}</h1>
                <b>{label}</b>
                <p style="font-size: 12px; margin-top: 8px;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    st.subheader("Test Results")

    if not speed_df.empty:
        grades_data = []
        for _, row in speed_df.iterrows():
            grade, desc = calculate_bufferbloat(row["download"], row["ping"])
            grades_data.append({
                "date": row["date"],
                "download": row["download"],
                "upload": row["upload"],
                "ping": row["ping"],
                "grade": grade,
                "description": desc
            })

        grades_df = pd.DataFrame(grades_data)

        col1, col2 = st.columns(2)

        with col1:
            grade_counts = grades_df["grade"].value_counts().reset_index()
            grade_counts.columns = ["grade", "count"]
            grade_order = ["A", "B", "C", "D", "F"]
            grade_counts["grade"] = pd.Categorical(
                grade_counts["grade"], categories=grade_order, ordered=True)
            grade_counts = grade_counts.sort_values("grade")

            colors = [grade_color(g) for g in grade_counts["grade"]]

            fig = go.Figure(go.Bar(
                x=grade_counts["grade"],
                y=grade_counts["count"],
                marker_color=colors
            ))
            fig.update_layout(title="Bufferbloat Grade Distribution")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            overall_grade, overall_desc = calculate_bufferbloat(
                speed_df["download"].mean(),
                speed_df["ping"].mean()
            )
            color = grade_color(overall_grade)

            st.markdown(f"""
            <div style="
                background-color: {color}22;
                border: 3px solid {color};
                border-radius: 15px;
                padding: 30px;
                text-align: center;
                margin-top: 20px;
            ">
                <p style="font-size: 18px; margin: 0;">Overall Bufferbloat Grade</p>
                <h1 style="color: {color}; font-size: 100px; margin: 10px 0;">{overall_grade}</h1>
                <p style="font-size: 16px;">{overall_desc}</p>
                <p style="color: #999; font-size: 13px;">
                    Based on avg download {speed_df["download"].mean():.1f} Mbps
                    and avg ping {speed_df["ping"].mean():.1f} ms
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        st.subheader("All Tests with Grades")

        def color_grade(val):
            colors_map = {
                "A": "background-color: #00CC9633",
                "B": "background-color: #7FBA0033",
                "C": "background-color: #FFD70033",
                "D": "background-color: #FF6B3533",
                "F": "background-color: #EF553B33"
            }
            return colors_map.get(val, "")

        st.dataframe(
            grades_df.style.applymap(color_grade, subset=["grade"]),
            use_container_width=True
        )

        st.divider()

        #Bufferbloat by time of day
        st.subheader("Bufferbloat by Time of Day")

        if "time_of_day" in speed_df.columns:
            time_data = speed_df[speed_df["time_of_day"].notna()].copy()

            if time_data.empty:
                st.info("No time of day data yet")
            else:
                time_data["grade"] = time_data.apply(
                    lambda row: calculate_bufferbloat(row["download"], row["ping"])[0], axis=1)

                time_order = ["Morning", "Afternoon", "Evening", "Night"]

                col1, col2 = st.columns(2)

                with col1:
                    ping_by_time = time_data.groupby("time_of_day")["ping"].mean().reset_index()
                    ping_by_time["time_of_day"] = pd.Categorical(
                        ping_by_time["time_of_day"], categories=time_order, ordered=True)
                    ping_by_time = ping_by_time.sort_values("time_of_day")

                    fig = px.bar(ping_by_time, x="time_of_day", y="ping",
                                 title="Average Ping by Time of Day (ms)",
                                 color="ping",
                                 color_continuous_scale="RdYlGn_r")
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    dl_by_time = time_data.groupby("time_of_day")["download"].mean().reset_index()
                    dl_by_time["time_of_day"] = pd.Categorical(
                        dl_by_time["time_of_day"], categories=time_order, ordered=True)
                    dl_by_time = dl_by_time.sort_values("time_of_day")

                    fig = px.bar(dl_by_time, x="time_of_day", y="download",
                                 title="Average Download by Time of Day (Mbps)",
                                 color="download",
                                 color_continuous_scale="Viridis")
                    st.plotly_chart(fig, use_container_width=True)

                col1, col2 = st.columns(2)

                with col1:
                    grade_by_time = time_data.groupby(
                        ["time_of_day", "grade"]).size().reset_index(name="count")

                    fig = px.bar(grade_by_time, x="time_of_day", y="count",
                                 color="grade",
                                 title="Bufferbloat Grades by Time of Day",
                                 category_orders={"time_of_day": time_order},
                                 color_discrete_map={
                                     "A": "#00CC96",
                                     "B": "#7FBA00",
                                     "C": "#FFD700",
                                     "D": "#FF6B35",
                                     "F": "#EF553B"
                                 })
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    best_time = ping_by_time.loc[ping_by_time["ping"].idxmin(), "time_of_day"]
                    worst_time = ping_by_time.loc[ping_by_time["ping"].idxmax(), "time_of_day"]

                    st.markdown("### Best Time to Use Internet")
                    st.success(f"**Best:** {best_time} — lowest average ping")
                    st.error(f"**Worst:** {worst_time} — highest average ping")

                    st.divider()

                    summary = time_data.groupby("time_of_day").agg({
                        "download": "mean",
                        "upload": "mean",
                        "ping": "mean"
                    }).round(2).reset_index()
                    summary.columns = ["Time of Day", "Avg Download", "Avg Upload", "Avg Ping"]
                    summary["Time of Day"] = pd.Categorical(
                        summary["Time of Day"], categories=time_order, ordered=True)
                    summary = summary.sort_values("Time of Day")
                    st.dataframe(summary, use_container_width=True)
        else:
            st.info("Run a new speed test to start collecting time of day data.")

#Trends
with tab3:
    st.subheader("Speed Trends")

    if speed_df.empty:
        st.warning("No data yet.")
        st.stop()

    speed_df["date"] = pd.to_datetime(speed_df["date"])

    st.subheader("Rolling Average (3 tests)")

    speed_df_sorted = speed_df.sort_values("date").copy()
    speed_df_sorted["download_avg"] = speed_df_sorted["download"].rolling(3).mean()
    speed_df_sorted["ping_avg"] = speed_df_sorted["ping"].rolling(3).mean()

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=speed_df_sorted["date"],
            y=speed_df_sorted["download"],
            name="Raw Download",
            mode="markers",
            marker=dict(color="#00CC96", size=6, opacity=0.5)
        ))
        fig.add_trace(go.Scatter(
            x=speed_df_sorted["date"],
            y=speed_df_sorted["download_avg"],
            name="3-Test Average",
            mode="lines",
            line=dict(color="#00CC96", width=3)
        ))
        fig.update_layout(title="Download Speed Trend")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=speed_df_sorted["date"],
            y=speed_df_sorted["ping"],
            name="Raw Ping",
            mode="markers",
            marker=dict(color="#EF553B", size=6, opacity=0.5)
        ))
        fig.add_trace(go.Scatter(
            x=speed_df_sorted["date"],
            y=speed_df_sorted["ping_avg"],
            name="3-Test Average",
            mode="lines",
            line=dict(color="#EF553B", width=3)
        ))
        fig.update_layout(title="Ping Trend")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Connection Health Over Time")

    half = len(speed_df_sorted) // 2
    first_half_avg = speed_df_sorted.iloc[:half]["download"].mean()
    second_half_avg = speed_df_sorted.iloc[half:]["download"].mean()
    trend_pct = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0

    first_half_ping = speed_df_sorted.iloc[:half]["ping"].mean()
    second_half_ping = speed_df_sorted.iloc[half:]["ping"].mean()
    ping_trend_pct = ((second_half_ping - first_half_ping) / first_half_ping * 100) if first_half_ping > 0 else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Download Trend",
            f"{second_half_avg:.1f} Mbps",
            delta=f"{trend_pct:.1f}% vs earlier",
            delta_color="normal"
        )
    with col2:
        st.metric(
            "Ping Trend",
            f"{second_half_ping:.1f} ms",
            delta=f"{ping_trend_pct:.1f}% vs earlier",
            delta_color="inverse"
        )
    with col3:
        if trend_pct > 5:
            st.success("Connection is improving")
        elif trend_pct < -5:
            st.error("Connection is getting worse")
        else:
            st.info("Connection is stable")

    st.divider()

    st.subheader("Monthly Averages")

    speed_df_sorted["month"] = speed_df_sorted["date"].dt.strftime("%Y-%m")
    monthly_avg = speed_df_sorted.groupby("month").agg({
        "download": "mean",
        "upload": "mean",
        "ping": "mean"
    }).reset_index()

    monthly_avg.columns = ["Month", "Avg Download", "Avg Upload", "Avg Ping"]
    monthly_avg = monthly_avg.round(2)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(monthly_avg, x="Month", y=["Avg Download", "Avg Upload"],
                     title="Monthly Average Speed",
                     barmode="group",
                     color_discrete_sequence=["#00CC96", "#AB63FA"])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(monthly_avg, x="Month", y="Avg Ping",
                      title="Monthly Average Ping",
                      markers=True,
                      color_discrete_sequence=["#EF553B"])
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(monthly_avg, use_container_width=True)