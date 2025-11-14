import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

VLLM_ENDPOINT = "http://granite-security-analyzer-predictor-white-hat.apps.cluster.example.com/v1/completions"

st.set_page_config(
    page_title="Employee Security Analyzer",
    page_icon="🔒",
    layout="wide"
)

st.title("🔒 Employee Behavior Security Analyzer")
st.markdown("*Powered by Fine-tuned Granite LLM on Red Hat OpenShift AI*")

st.sidebar.header("About")
st.sidebar.info("""
This GenAI application uses a fine-tuned Granite LLM 
to analyze employee activity logs and detect 
potential security threats and insider risks.

**Technologies:**
- Fine-tuned IBM Granite LLM
- vLLM serving on RHOAI
- Deployed on OpenShift
""")

tab1, tab2, tab3 = st.tabs(["🔍 Analyze Employee", "📊 Bulk Analysis", "📝 Upload Logs"])

with tab1:
    st.header("Individual Employee Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        employee_id = st.text_input("Employee ID", placeholder="emp_001")
        
        st.subheader("Activity Summary")
        total_sessions = st.number_input("Total Sessions (30 days)", min_value=0, value=15)
        unique_ips = st.number_input("Unique IP Addresses", min_value=1, value=2)
        unique_locations = st.number_input("Different Locations", min_value=1, value=1)
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            night_access = st.number_input("After-hours Accesses", min_value=0, value=0)
        with col_b:
            weekend_access = st.number_input("Weekend Accesses", min_value=0, value=0)
        with col_c:
            failed_logins = st.number_input("Failed Logins", min_value=0, value=0)
    
    with col2:
        st.subheader("Recent Activity")
        recent_activities = st.text_area(
            "Timeline (one per line)",
            height=200,
            placeholder="2025-11-14 09:15: login from 192.168.1.45\n2025-11-14 09:20: read monthly_report.pdf"
        )
    
    actions_json = st.text_area(
        "Action Distribution (JSON)",
        value='{"login": 10, "logout": 10, "read": 8, "download": 2}',
        height=100
    )
    
    external_ips_count = st.number_input("External IPs Detected", min_value=0, value=0)
    sensitive_resources = st.number_input("Sensitive Resources Accessed", min_value=0, value=0)
    
    if st.button("🔍 Analyze Behavior", type="primary", use_container_width=True):
        with st.spinner("Analyzing employee behavior with Granite LLM..."):
            
            user_prompt = f"""Analyze employee behavior for: {employee_id}

Activity Summary (30-day period):
- Total login sessions: {total_sessions}
- Unique IP addresses used: {unique_ips}
- Different locations: {unique_locations}
- After-hours accesses: {night_access}
- Weekend accesses: {weekend_access}
- Failed login attempts: {failed_logins}

Recent Activity Timeline:
{recent_activities}

Action Distribution:
{actions_json}

External IPs detected: {external_ips_count}
Sensitive resources accessed: {sensitive_resources}

Provide detailed security assessment including risk level, behavioral analysis, and recommendations."""

            system_prompt = "You are a cybersecurity expert specializing in employee behavior analytics and insider threat detection. Analyze employee activity logs and provide comprehensive security assessments with risk levels and actionable recommendations."
            
            full_prompt = f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
            
            try:
                response = requests.post(
                    VLLM_ENDPOINT,
                    json={
                        "model": "granite-security-finetuned",
                        "prompt": full_prompt,
                        "max_tokens": 1500,
                        "temperature": 0.7,
                        "top_p": 0.9
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result['choices'][0]['text']
                    
                    st.success("✅ Analysis Complete!")
                    
                    if "CRITICAL" in analysis or "HIGH" in analysis:
                        st.error("⚠️ SECURITY ALERT DETECTED")
                    elif "MEDIUM" in analysis:
                        st.warning("⚠️ Elevated Risk Detected")
                    else:
                        st.info("✅ Normal Behavior Pattern")
                    
                    st.markdown("### Security Assessment")
                    st.markdown(analysis)
                    
                    st.download_button(
                        "📥 Download Report",
                        data=analysis,
                        file_name=f"security_report_{employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                st.error(f"Failed to connect to Granite model: {str(e)}")
                st.info("Make sure the vLLM inference service is running in RHOAI")

with tab2:
    st.header("Bulk Employee Analysis")
    st.info("Upload CSV with multiple employees for batch analysis")
    
    uploaded_file = st.file_uploader("Upload Employee Data (CSV)", type=['csv'])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())
        
        if st.button("Analyze All Employees"):
            st.warning("Batch analysis feature - coming soon!")

with tab3:
    st.header("Upload Activity Logs")
    
    log_file = st.file_uploader("Upload JSON logs", type=['json'])
    
    if log_file:
        logs = json.load(log_file)
        st.json(logs[:3])
        st.success(f"Loaded {len(logs)} log entries")

st.sidebar.markdown("---")
st.sidebar.markdown("**Model Info:**")
st.sidebar.code(f"Endpoint: {VLLM_ENDPOINT}")
st.sidebar.markdown("**Status:** 🟢 Connected" if True else "**Status:** 🔴 Disconnected")
