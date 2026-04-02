import streamlit as st
import pandas as pd
import plotly.express as px
from database import create_connection, create_tables

create_tables()

st.set_page_config(page_title="Internet", page_icon="🌐", layout="wide")
st.title("🌐 Internet Speed & Ping Tracker")
st.divider()

#Manual speed test entry 
# st.subheader("Add Manual Speed Test")

# col1, col2, col3, col4 = st.columns(4)

# with col1:
#     date = st.date_input("Date")
# with col2:
#     download = st.number_input("Download (Mbps)", min_value=0.0, step=0.1)
# with col3:
#     upload = st.number_input("Upload (Mbps)", min_value=0.0, step=0.1)
# with col4:
#     ping = st.number_input("Ping (ms)", min_value=0.0, step=0.1)

# if st.button("💾 Save Manual Entry"):
#     conn = create_connection()
#     cursor = conn.cursor()
#     cursor.execute("""
#         INSERT INTO internet_speed (date, download, upload, ping)
#         VALUES (?, ?, ?, ?)
#     """, (str(date), download, upload, ping))
#     conn.commit()
#     conn.close()
#     st.success("Speed test saved!")
#     st.rerun()

# st.divider()

#speed test 
st.subheader("🚀 Run Live Speed Test")
st.caption("Runs a real speed test and saves result automatically")

if st.button("▶️ Start Speed Test Now"):
    with st.spinner("Running speed test... this takes 15-30 seconds"):
        try:
            import speedtest
            s = speedtest.Speedtest()
            s.get_best_server()
            download_speed = s.download() / 1_000_000
            upload_speed = s.upload() / 1_000_000
            ping_result = s.results.ping

            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO internet_speed (date, download, upload, ping)
                VALUES (?, ?, ?, ?)
            """, (pd.Timestamp.now().strftime("%Y-%m-%d"), 
                  round(download_speed, 2),
                  round(upload_speed, 2), 
                  round(ping_result, 2)))
            conn.commit()
            conn.close()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Download", f"{download_speed:.1f} Mbps")
            with col2:
                st.metric("Upload", f"{upload_speed:.1f} Mbps")
            with col3:
                st.metric("Ping", f"{ping_result:.1f} ms")

            st.success("Speed test complete and saved!")
            st.rerun()

        except ImportError:
            st.error("speedtest-cli not installed. Run: pip install speedtest-cli")
        except Exception as e:
            st.error(f"Speed test failed: {e}")

st.divider()

#Load data
conn = create_connection()
speed_df = pd.read_sql_query("SELECT * FROM internet_speed ORDER BY date", conn)
conn.close()

if speed_df.empty:
    st.warning("No speed data yet. Add your first entry above.")
else:
    #Metrics
    st.subheader("📊 Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_download = speed_df["download"].mean()
        st.metric("Avg Download", f"{avg_download:.1f} Mbps")

    with col2:
        avg_upload = speed_df["upload"].mean()
        st.metric("Avg Upload", f"{avg_upload:.1f} Mbps")

    with col3:
        avg_ping = speed_df["ping"].mean()
        st.metric("Avg Ping", f"{avg_ping:.1f} ms")

    with col4:
        best_ping = speed_df["ping"].min()
        st.metric("Best Ping", f"{best_ping:.1f} ms")

    st.divider()

    #Charts
    st.subheader("📈 Charts")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(speed_df, x="date", y=["download", "upload"],
                      title="Download & Upload Speed (Mbps)",
                      markers=True,
                      color_discrete_sequence=["#00CC96", "#AB63FA"])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(speed_df, x="date", y="ping",
                      title="Ping Over Time (ms)",
                      markers=True,
                      color_discrete_sequence=["#EF553B"])
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(speed_df, x="date", y="download",
                     title="Download Speed Per Test",
                     color_discrete_sequence=["#00CC96"])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.scatter(speed_df, x="download", y="ping",
                         title="Download Speed vs Ping",
                         color_discrete_sequence=["#FF6B35"])
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    #Raw data
    st.subheader("📋 Raw Data")
    st.dataframe(speed_df, use_container_width=True)
