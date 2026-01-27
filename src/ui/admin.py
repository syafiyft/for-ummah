import streamlit as st
import requests
import pandas as pd
import plotly.express as px

def show_admin_page(api_url):
    # Header with Status Badge
    col_header, col_status = st.columns([0.8, 0.2])
    with col_header:
        st.title("Admin Dashboard")
        st.caption("Monitor system status and trigger updates.")
    with col_status:
        try:
            h_resp = requests.get(f"{api_url}/health", timeout=2)
            if h_resp.status_code == 200:
                st.markdown('<span style="background-color:#28a745;padding:4px 8px;border-radius:4px;color:white;font-size:12px;">backend online</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span style="background-color:#dc3545;padding:4px 8px;border-radius:4px;color:white;font-size:12px;">backend offline</span>', unsafe_allow_html=True)
        except:
             st.markdown('<span style="background-color:#dc3545;padding:4px 8px;border-radius:4px;color:white;font-size:12px;">backend offline</span>', unsafe_allow_html=True)
    
    st.divider()
    
    # 1. System Stats (Compact)
    # Fetch data
    doc_count = 0
    total_size = 0.0
    last_update = "-"
    try:
        resp = requests.get(f"{api_url}/pdf/list", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            doc_count = data.get("count", 0)
            total_size = sum(d["size_bytes"] for d in data.get("pdfs", [])) / (1024*1024)
            
        hist_resp = requests.get(f"{api_url}/history/sources", timeout=3)
        if hist_resp.status_code == 200:
            hist = hist_resp.json()
            if hist:
                last_update = hist[0]["timestamp"].split(".")[0].replace("T", " ")
    except: pass
    
    # Display Stats using simple columns
    sc1, sc2, sc3 = st.columns(3)
    sc1.markdown(f"**Indexed:** {doc_count}")
    sc2.markdown(f"**Storage:** {total_size:.2f} MB")
    sc3.markdown(f"**Last Update:** {last_update}")
    st.markdown("---")
    
    # 2. Automated Scraper
    st.subheader("Automated Scraper")
    
    # Source Selection
    c1, c2, c3 = st.columns(3)
    use_bnm = c1.checkbox("BNM", value=True)
    use_sc = c2.checkbox("SC", value=True)
    use_aaoifi = c3.checkbox("AAOIFI", value=True)
    
    if st.button("Trigger Update Now", type="primary"):
        sources = []
        if use_bnm: sources.append("BNM")
        if use_sc: sources.append("SC")
        if use_aaoifi: sources.append("AAOIFI")
        
        try:
            resp = requests.post(f"{api_url}/admin/trigger-update", json={"sources": sources}, timeout=5)
            if resp.status_code == 200:
                st.toast(f"Job Started! ID: {resp.json().get('job_id')}")
            else:
                st.error(f"Failed: {resp.text}")
        except Exception as e:
            st.error(f"Error: {e}")

    # Live Status Polling
    try:
        status_resp = requests.get(f"{api_url}/admin/job-status", timeout=2)
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            status_state = status_data.get("status", "idle")
            
            if status_state == "running":
                st.progress(status_data.get("progress", 0.0))
                st.caption(f"{status_data.get('message', 'Processing...')}")
            elif status_state == "completed":
                st.success(f"Last Run: {status_data.get('message')}")
            elif status_state == "failed":
                st.error(f"Last Run Failed: {status_data.get('message')}")
    except: pass

    # 3. Ingestion History
    st.divider()
    
    # Header for Table
    th1, th2 = st.columns([0.8, 0.2])
    with th1:
        st.subheader("Ingestion History")
    with th2:
        if st.button("Refresh Logs"): st.rerun()

    try:
        resp = requests.get(f"{api_url}/history/sources", timeout=5)
        if resp.status_code == 200:
            history = resp.json()
            if history:
                df = pd.DataFrame(history)
                if "timestamp" in df.columns:
                    # Convert to datetime
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    # If naive, localize to UTC (assuming backend stores UTC)
                    if df["timestamp"].dt.tz is None:
                        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
                    # Convert to Malaysia time
                    df["timestamp"] = df["timestamp"].dt.tz_convert("Asia/Kuala_Lumpur").dt.strftime("%Y-%m-%d %H:%M:%S")
                    
                # Clean table columns
                st.dataframe(
                    df[["timestamp", "source", "filename", "status"]], 
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No history found.")
    except:
        st.caption("Unable to load history.")


