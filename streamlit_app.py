"""Streamlit front-end. This is the file Streamlit Cloud runs.

Local:  streamlit run streamlit_app.py
"""

import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

st.set_page_config(page_title="AI Research Agent", page_icon="🔎", layout="centered")


# --------------------------------------------------------------------------
# API key: from .env when local, from st.secrets when deployed.
# CrewAI reads the key from the environment, so we copy it there either way.
# --------------------------------------------------------------------------
def load_api_key() -> bool:
    load_dotenv()  # local .env file
    if os.getenv("GROQ_API_KEY"):
        return True
    try:
        key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return False
    if key:
        os.environ["GROQ_API_KEY"] = key
        return True
    return False


key_found = load_api_key()

# Import AFTER the key is set, so CrewAI picks it up.
from research_crew import AVAILABLE_MODELS, run_research  # noqa: E402


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------
st.title("🔎 AI Research Agent")
st.caption("One CrewAI agent · DuckDuckGo search · Groq inference")

if not key_found:
    st.error(
        "**No GROQ_API_KEY found.**\n\n"
        "Local: create a `.env` file with `GROQ_API_KEY=gsk_...`\n\n"
        "Deployed: add it under *Settings → Secrets* in Streamlit Cloud.\n\n"
        "Get a free key at https://console.groq.com/keys"
    )
    st.stop()

with st.sidebar:
    st.header("Settings")
    model_label = st.selectbox("Model", list(AVAILABLE_MODELS.keys()))
    model = AVAILABLE_MODELS[model_label]
    searches = st.slider(
        "Search depth", 2, 8, 4,
        help="Roughly how many searches the agent runs. More = better report, slower.",
    )
    st.divider()
    st.caption(
        "DuckDuckGo sometimes rate-limits cloud IPs. If a run comes back thin, "
        "wait a minute and try again."
    )

topic = st.text_input(
    "Research topic",
    placeholder="e.g. the state of solid-state batteries in 2026",
)
context = st.text_area(
    "Extra instructions (optional)",
    placeholder="e.g. Focus on cost, not chemistry. Audience: a non-technical investor.",
    height=80,
)

if st.button("Run research", type="primary", disabled=not topic.strip()):
    with st.spinner("Searching, reading, and writing… this takes 1-3 minutes."):
        try:
            report = run_research(
                topic=topic.strip(),
                context=context.strip(),
                model=model,
                searches=searches,
            )
            st.session_state["report"] = report
            st.session_state["topic"] = topic.strip()
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.info(
                "Common causes: Groq rate limit (wait 60s), an invalid API key, "
                "or DuckDuckGo blocking the request."
            )

if "report" in st.session_state:
    st.divider()
    st.markdown(st.session_state["report"])

    safe = "".join(c if c.isalnum() else "-" for c in st.session_state["topic"])[:40]
    st.download_button(
        "Download report (.md)",
        data=st.session_state["report"],
        file_name=f"{datetime.now():%Y%m%d}-{safe}.md",
        mime="text/markdown",
    )
