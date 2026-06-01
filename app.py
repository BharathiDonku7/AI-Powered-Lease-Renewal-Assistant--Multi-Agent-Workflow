"""
Streamlit UI — supports both structured JSON residents and PDF uploads.
"""
import json
import tempfile
import streamlit as st
from dotenv import load_dotenv
from orchestrator import process_renewal, process_renewal_from_pdf

load_dotenv()

st.set_page_config(page_title="Lease Renewal Agents", layout="wide")
st.title("🏢 Multi-Agent Lease Renewal Assistant")
st.caption("Agentic AI workflow with document ingestion, compliance guardrails, and personalized communication")

if "review_queue" not in st.session_state:
    st.session_state.review_queue = []

st.sidebar.header("📋 Human Review Queue")
if not st.session_state.review_queue:
    st.sidebar.caption("No items pending review.")
else:
    for item in st.session_state.review_queue:
        st.sidebar.markdown(f"**{item['resident_name']}** — {item['final_status']}")

tab1, tab2 = st.tabs(["📄 Upload Document", "📋 Use Sample Residents"])

with tab1:
    st.subheader("Ingest an Unstructured Rental Application or Lease")
    uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded and st.button("Run Workflow from Document", type="primary", key="pdf_run"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name
        with st.spinner("Document Ingestion Agent + downstream agents running..."):
            trace = process_renewal_from_pdf(tmp_path)
        _render_trace(trace) if False else None  # placeholder to keep linear flow

        status = trace["final_status"]
        if status == "auto_approved_and_sent":
            st.success(f"✅ Final Status: {status}")
        elif "pending_human_review" in status:
            st.warning(f"⚠️ Final Status: {status}")
            st.session_state.review_queue.append({
                "resident_name": trace.get("resident_name", "Unknown"),
                "final_status": status
            })
        else:
            st.error(f"🚫 Final Status: {status}")

        st.divider()
        st.subheader("Agent Reasoning Trace")
        for step in trace["steps"]:
            with st.expander(f"🤖 {step['agent']}", expanded=False):
                st.json(step["output"])

        comm_step = next((s for s in trace["steps"] if s["agent"] == "CommunicationAgent"), None)
        if comm_step and "body" in comm_step["output"]:
            st.divider()
            st.subheader("✉️ Drafted Renewal Communication")
            out = comm_step["output"]
            st.markdown(f"**Channel:** {out['channel']}")
            st.markdown(f"**Subject:** {out['subject']}")
            st.text_area("Message Body", out["body"], height=200)
            st.caption(f"Tone notes: {out['tone_notes']}")

with tab2:
    with open("data/residents.json") as f:
        residents = json.load(f)["residents"]

    names = [f"{r['name']} ({r['resident_id']})" for r in residents]
    selected = st.selectbox("Select a resident:", names)
    selected_resident = residents[names.index(selected)]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Resident Snapshot")
        st.json(selected_resident)

    if st.button("Run Renewal Workflow", type="primary", key="json_run"):
        with st.spinner("Agents are working..."):
            trace = process_renewal(selected_resident)

        with col2:
            status = trace["final_status"]
            if status == "auto_approved_and_sent":
                st.success(f"✅ Final Status: {status}")
            elif status == "pending_human_review":
                st.warning(f"⚠️ Final Status: {status}")
                st.session_state.review_queue.append({
                    "resident_name": trace["resident_name"],
                    "final_status": status
                })
            else:
                st.error(f"🚫 Final Status: {status}")

        st.divider()
        st.subheader("Agent Reasoning Trace")
        for step in trace["steps"]:
            with st.expander(f"🤖 {step['agent']}", expanded=False):
                st.json(step["output"])

        comm_step = next((s for s in trace["steps"] if s["agent"] == "CommunicationAgent"), None)
        if comm_step and "body" in comm_step["output"]:
            st.divider()
            st.subheader("✉️ Drafted Renewal Communication")
            out = comm_step["output"]
            st.markdown(f"**Channel:** {out['channel']}")
            st.markdown(f"**Subject:** {out['subject']}")
            st.text_area("Message Body", out["body"], height=200)
            st.caption(f"Tone notes: {out['tone_notes']}")