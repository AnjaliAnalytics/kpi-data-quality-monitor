import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yaml
import os
import json
from src.database import supabase

# Page Configuration
st.set_page_config(
    page_title="KPI Data Quality & Observability Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (CSS)
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 14px;
        color: #6c757d;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #212529;
    }
    /* Severity Badges */
    .badge-critical {
        background-color: #f8d7da;
        color: #721c24;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 12px;
    }
    .badge-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 12px;
    }
    .badge-passed {
        background-color: #d4edda;
        color: #155724;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Cache Metrics Config
@st.cache_data
def load_metrics_config():
    config_path = os.path.join("config", "metrics.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f).get("metrics", [])
    return []

# Fetch Data Helper
@st.cache_data(ttl=30)
def fetch_data(table_name, select="*", order_col=None, desc=True):
    try:
        query = supabase.table(table_name).select(select)
        if order_col:
            query = query.order(order_col, desc=desc)
        res = query.execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()

metrics_config = load_metrics_config()

# Sidebar Setup
st.sidebar.image("https://img.icons8.com/color/96/dashboard--v1.png", width=60)
st.sidebar.title("Data Observability")
st.sidebar.caption("Real-Time KPI Health & AI Root-Cause Engine")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation Menu",
    ["Overview", "KPI Monitoring", "Anomalies", "Data Quality", "Alert History", "Semantic Metrics", "About Project"]
)

# ==========================================
# 1. OVERVIEW PAGE
# ==========================================
if page == "Overview":
    st.title("📊 Platform Executive Summary")
    st.markdown("High-level overview of system status, data freshness, active anomalies, and current business metrics.")
    st.markdown("---")

    runs_df = fetch_data("monitoring_runs", order_col="run_timestamp", desc=True)
    metric_res_df = fetch_data("metric_results", order_col="evaluated_at", desc=True)
    anomalies_df = fetch_data("anomalies", order_col="detected_at", desc=True)

    # Key Indicator Cards
    col1, col2, col3, col4 = st.columns(4)
    
    last_run_time = "Never Executed"
    dq_status = "UNKNOWN"
    if not runs_df.empty:
        latest_run = runs_df.iloc[0]
        last_run_time = str(latest_run.get("run_timestamp", ""))[:19].replace("T", " ")
        dq_status = "PASSED ✅" if latest_run.get("data_quality_passed") else "ATTENTION REQ. ❌"

    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Last Audit Time</div><div class="metric-value" style="font-size: 18px;">{last_run_time}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Data Quality Health</div><div class="metric-value" style="font-size: 20px;">{dq_status}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Monitored KPIs</div><div class="metric-value">{len(metrics_config)}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Active Anomalies</div><div class="metric-value" style="color: #dc3545;">{len(anomalies_df)}</div></div>', unsafe_allow_html=True)

    st.markdown("### 📌 Live KPI Health Status")
    if not metric_res_df.empty:
        latest_metrics = metric_res_df.sort_values("metric_date", ascending=False).drop_duplicates(subset=["metric_name"])
        cols = st.columns(3)
        for idx, (_, row) in enumerate(latest_metrics.iterrows()):
            with cols[idx % 3]:
                is_anom = row["is_anomaly"]
                border_color = "#dc3545" if is_anom else "#28a745"
                status_badge = "🚨 ANOMALY" if is_anom else "✅ NORMAL"
                
                st.markdown(f"""
                <div style="border-left: 5px solid {border_color}; background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; color: #333;">{row['metric_name'].replace('_', ' ').title()}</span>
                        <span style="font-size: 12px; font-weight: bold; color: {border_color};">{status_badge}</span>
                    </div>
                    <div style="font-size: 24px; font-weight: bold; margin: 8px 0;">{row['current_value']:,.2f}</div>
                    <div style="font-size: 13px; color: #6c757d;">Date: {row['metric_date']} | Change: <b>{row['percentage_change']}%</b></div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No metric evaluations recorded yet.")

# ==========================================
# 2. KPI MONITORING PAGE
# ==========================================
elif page == "KPI Monitoring":
    st.title("📈 KPI Time-Series & Statistical Baselines")
    st.markdown("Compare actual daily values against expected statistical baselines and inspect detected anomaly trigger points.")

    metric_res_df = fetch_data("metric_results", order_col="metric_date", desc=False)

    if not metric_res_df.empty:
        metric_names = metric_res_df["metric_name"].unique()
        selected_metric = st.selectbox("🎯 Select Metric to Visualize", metric_names)

        filtered_df = metric_res_df[metric_res_df["metric_name"] == selected_metric]

        fig = go.Figure()
        # Baseline Line
        fig.add_trace(go.Scatter(
            x=filtered_df["metric_date"], y=filtered_df["expected_baseline"],
            mode='lines', name='Expected Baseline', line=dict(color='#ffc107', width=2, dash='dash')
        ))
        # Actual Line
        fig.add_trace(go.Scatter(
            x=filtered_df["metric_date"], y=filtered_df["current_value"],
            mode='lines+markers', name='Actual Value', line=dict(color='#0d6efd', width=3)
        ))
        # Anomaly Scatter Markers
        anom_subset = filtered_df[filtered_df["is_anomaly"] == True]
        if not anom_subset.empty:
            fig.add_trace(go.Scatter(
                x=anom_subset["metric_date"], y=anom_subset["current_value"],
                mode='markers', name='Anomaly Flagged', marker=dict(color='#dc3545', size=14, symbol='x')
            ))

        fig.update_layout(
            title=f"Performance Trajectory: {selected_metric.replace('_', ' ').title()}",
            xaxis_title="Date", yaxis_title="Metric Value",
            template="plotly_white", hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Historical Snapshot Table")
        st.dataframe(filtered_df[["metric_date", "current_value", "expected_baseline", "percentage_change", "is_anomaly", "severity"]], use_container_width=True)

# ==========================================
# 3. ANOMALIES PAGE
# ==========================================
elif page == "Anomalies":
    st.title("🚨 Detected Incidents & Gemini AI Root-Cause Analysis")
    st.markdown("Detailed breakdown of statistical anomalies flagged by the system, complete with AI explanations and investigation guidance.")

    anomalies_df = fetch_data("anomalies", order_col="detected_at", desc=True)

    if not anomalies_df.empty:
        for _, row in anomalies_df.iterrows():
            sev = row['severity']
            badge_class = "badge-critical" if sev == "CRITICAL" else "badge-warning"
            
            st.markdown(f"""
            <div style="border: 1px solid #ffc9c9; background-color: #fff5f5; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: #b02a37;">🚨 {row['metric_name'].replace('_', ' ').title()} Anomaly Flagged</h3>
                    <span class="{badge_class}">{sev} SEVERITY</span>
                </div>
                <p style="color: #6c757d; margin-top: 5px;">Detected At: {str(row['detected_at'])[:19].replace('T', ' ')}</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Observed Value", f"{row['current_value']:,.2f}")
            col2.metric("Expected Baseline", f"{row['expected_baseline']:,.2f}")
            col3.metric("Percentage Deviation", f"{row['percentage_change']}%")

            ai_exp = row.get("ai_explanation", {})
            if isinstance(ai_exp, str):
                try: ai_exp = json.loads(ai_exp)
                except: ai_exp = {}

            st.markdown("#### 🤖 AI Root Cause Interpretation")
            st.info(ai_exp.get("summary", "No AI summary provided."))

            col_sig, col_act = st.columns(2)
            with col_sig:
                st.markdown("**📊 Contributing Signals:**")
                for sig in ai_exp.get("possible_contributing_signals", ["No signals listed."]):
                    st.markdown(f"- {sig}")

            with col_act:
                st.markdown("**🛠️ Recommended Investigation Steps:**")
                actions = ai_exp.get("recommended_investigation", ai_exp.get("recommended_actions", ["No actions listed."]))
                for act in actions:
                    st.markdown(f"- {act}")
            st.markdown("---")
    else:
        st.success("🎉 No anomalies present in audit history.")

# ==========================================
# 4. DATA QUALITY PAGE
# ==========================================
elif page == "Data Quality":
    st.title("🛡️ Data Quality & Freshness Verification Suite")
    st.markdown("Automated validation results covering data freshness, missing values, duplicate IDs, and range bounds.")

    dq_df = fetch_data("data_quality_results", order_col="checked_at", desc=True)

    if not dq_df.empty:
        passed_count = len(dq_df[dq_df["passed"] == True])
        total_checks = len(dq_df)
        
        col1, col2 = st.columns(2)
        col1.metric("Overall Suite Pass Rate", f"{passed_count} / {total_checks} Checks Passed")
        col2.metric("Latest Audit Timestamp", str(dq_df.iloc[0]["checked_at"])[:19].replace("T", " "))

        st.markdown("---")
        st.subheader("📋 Individual Rule Execution Audit Log")

        for _, row in dq_df.iterrows():
            passed = row["passed"]
            icon = "✅ PASSED" if passed else "❌ FAILED"
            color = "#198754" if passed else "#dc3545"
            raw_title = str(row.get("check_name", "Data Check")).replace("_", " ").title()

            with st.expander(f"{icon} | {raw_title} ({str(row['checked_at'])[:19].replace('T', ' ')})"):
                details = row.get("details", {})
                if isinstance(details, str):
                    try: details = json.loads(details)
                    except: details = {}

                st.markdown(f"<span style='color: {color}; font-weight: bold;'>Check Status: {icon}</span>", unsafe_allow_html=True)
                st.markdown("**Check Payload & Metrics:**")
                st.json(details if details else {"status": passed})
    else:
        st.info("No data quality checks recorded. Run `python scripts/seed_demo_data.py` to insert test audit records.")

# ==========================================
# 5. ALERT HISTORY PAGE
# ==========================================
elif page == "Alert History":
    st.title("🔔 Slack Notification Delivery Logs")
    st.markdown("Audit log tracking incoming webhook alerts sent to team Slack channels.")

    anomalies_df = fetch_data("anomalies", order_col="detected_at", desc=True)
    if not anomalies_df.empty:
        display_df = anomalies_df[["metric_name", "severity", "slack_alert_sent", "detected_at"]].copy()
        display_df.columns = ["Metric Name", "Severity Level", "Slack Alert Dispatched", "Timestamp"]
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No alert dispatch history logged yet.")

# ==========================================
# 6. SEMANTIC METRICS PAGE
# ==========================================
elif page == "Semantic Metrics":
    st.title("📖 Semantic Metrics Definition Layer")
    st.markdown("Business definitions, mathematical logic, metric owners, and anomaly parameters defined in `config/metrics.yaml`.")

    if metrics_config:
        for m in metrics_config:
            with st.expander(f"📌 {m.get('display_name', m.get('name'))} (`{m.get('name')}`)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Description:** {m.get('description', 'N/A')}")
                    st.markdown(f"**Metric Owner:** `{m.get('owner', 'N/A')}`")
                    st.markdown(f"**SQL Source View:** `{m.get('sql_view', 'N/A')}`")
                with col2:
                    st.markdown(f"**Detection Method:** `{m.get('anomaly_config', {}).get('method', 'N/A')}`")
                    st.markdown(f"**Z-Threshold:** `{m.get('anomaly_config', {}).get('sensitivity_zscore', 'N/A')}`")
                    st.markdown(f"**Min Change Threshold:** `{m.get('anomaly_config', {}).get('min_change_percent', 'N/A')}%`")
    else:
        st.warning("Could not read `config/metrics.yaml`.")

# ==========================================
# 7. ABOUT PROJECT PAGE
# ==========================================
elif page == "About Project":
    st.title("ℹ️ About the Observability Platform")
    st.markdown("""
    ### Production-Grade KPI Data Quality & Observability Platform
    An automated end-to-end data health and observability pipeline designed to detect data drift, statistical anomalies, and schema issues before they impact business logic.

    #### 🛠️ Technology Stack:
    - **Backend & Storage:** Python, Supabase (PostgreSQL, REST API)
    - **Semantic Engine:** Declarative YAML (`metrics.yaml`)
    - **Statistical Detection:** Quantitative Z-Score & Interquartile Range (IQR) Baselines
    - **AI Incident Interpretation:** Gemini API (`gemini-3.8-flash`)
    - **Real-Time Alerting:** Slack Incoming Webhooks (Block Kit UI)
    - **Observability UI:** Streamlit & Plotly
    """)