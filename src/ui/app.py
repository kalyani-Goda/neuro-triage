"""Streamlit frontend for Neuro-Triage."""

import streamlit as st
import requests
import json
from datetime import datetime

# Configuration
st.set_page_config(
    page_title="Neuro-Triage",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styling
st.markdown(
    """
    <style>
    .stAlert { margin-top: 1rem; }
    .response-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .emergency { background-color: #fee; border-color: #c33; }
    .urgent { background-color: #fef8e7; border-color: #d4a500; }
    .routine { background-color: #e8f5e9; border-color: #2e7d32; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title
st.title("🏥 Neuro-Triage")
st.markdown(
    "**Clinical Decision Support System** | PARM Framework | Multi-Agent Reflection"
)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    api_url = st.text_input(
        "API URL",
        value="http://localhost:8000",
        help="FastAPI backend URL",
    )

    st.divider()

    st.header("📋 Patient Information")
    patient_id = st.text_input(
        "Patient ID",
        value="patient_001",
        help="Unique patient identifier",
    )

    st.divider()

    st.header("ℹ️ About")
    st.markdown(
        """
        **Neuro-Triage** is a reflective, multi-agent clinical decision support system.

        **Key Features:**
        - 🧠 System 2 Thinking (Critic Agent)
        - 🛡️ Safety Guardrails
        - 📚 RAG with Medical Knowledge
        - 💾 Patient Memory System
        - 📊 Observability

        **Research Foundation:**
        - PARM Framework
        - Dual-Loop Verification
        - Clinical Safety Thresholds
        """
    )


# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Clinical Consultation")

    # Input section
    with st.form("consultation_form"):
        patient_message = st.text_area(
            "Describe symptoms or clinical concern:",
            placeholder="e.g., 'Patient reports severe chest pain and shortness of breath'",
            height=100,
        )

        submitted = st.form_submit_button("🔄 Analyze", use_container_width=True)

    if submitted and patient_message:
        with st.spinner("🔍 Processing through PARM workflow..."):
            try:
                # Call API
                response = requests.post(
                    f"{api_url}/chat",
                    json={
                        "patient_id": patient_id,
                        "message": patient_message,
                    },
                    timeout=30,
                )

                if response.status_code == 200:
                    result = response.json()

                    # Display triage level
                    st.divider()
                    col_triage, col_score = st.columns(2)

                    with col_triage:
                        triage_level = result.get("triage_level", "unknown").upper()
                        if triage_level == "EMERGENCY":
                            st.error(f"🚨 **EMERGENCY ALERT**")
                        elif triage_level == "URGENT":
                            st.warning(f"⚠️ **URGENT** - {triage_level}")
                        else:
                            st.info(f"✅ **ROUTINE** - {triage_level}")

                    with col_score:
                        score = result.get("critique_score", 0)
                        st.metric(
                            "Safety Score",
                            f"{score}/5",
                            delta="✓ Approved" if score >= 4 else "⚠️ Needs Review",
                        )

                    # Display response
                    st.divider()
                    st.subheader("📋 Clinical Response")
                    response_text = result.get("final_response", "")
                    if result.get("triage_level") == "emergency":
                        st.error(response_text)
                    else:
                        st.info(response_text)

                    # Thought process (expandable)
                    with st.expander("🧠 Thought Process"):
                        st.markdown(
                            f"""
                        **Triage Analysis:**
                        - Level: {result.get("triage_level")}
                        - Confidence: {result.get("triage_confidence", 0):.1%}

                        **Reflection Details:**
                        - Critique Feedback: {result.get("critique_feedback", "N/A")}
                        - Iterations: {result.get("reflection_iterations", 0)}
                        - Safety Violations: {", ".join(result.get("safety_violations", [])) or "None"}

                        **Performance Metrics:**
                        - Status: {result.get("response_status")}
                        - Session ID: `{result.get("session_id")}`
                        """
                        )

                else:
                    st.error(f"API Error: {response.status_code}")
                    st.error(response.text)

            except requests.exceptions.ConnectionError:
                st.error(
                    "❌ Cannot connect to API. Make sure the backend is running at "
                    f"{api_url}"
                )
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

with col2:
    st.header("📊 Metrics")

    # Health check
    try:
        health_response = requests.get(f"{api_url}/health", timeout=5)
        if health_response.status_code == 200:
            health = health_response.json()
            st.subheader("System Status")

            col_db, col_vec, col_cache = st.columns(3)
            with col_db:
                st.metric("Database", "✅" if health["database"] else "❌")

            with col_vec:
                st.metric("Vector DB", "✅" if health["qdrant"] else "❌")

            with col_cache:
                st.metric("Cache", "✅" if health["redis"] else "❌")
        else:
            st.warning("Health check unavailable")
    except:
        st.warning("Cannot connect to backend")

    # Statistics placeholder
    st.subheader("📈 Session Stats")
    st.info(
        """
        **Coming soon:**
        - Hallucination Rate
        - Triage Recall
        - Latency Metrics
        """
    )


# Footer
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.85rem;">
    <p>Neuro-Triage v0.1.0 | Research Implementation | Not for clinical use without validation</p>
    </div>
    """,
    unsafe_allow_html=True,
)
