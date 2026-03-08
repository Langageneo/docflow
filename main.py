"""
DocFlow — Assistant Bureautique Intelligent
"""

import streamlit as st
from app.database.db import init_db
from app.i18n import get_translations

st.set_page_config(
    page_title="DocFlow",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

if "lang" not in st.session_state:
    st.session_state["lang"] = "fr"
if "user_id" not in st.session_state:
    st.session_state["user_id"] = 1
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "dashboard"

T = get_translations(st.session_state["lang"])

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap');

:root {
    --bg: #0d1b2a;
    --card: #16213e;
    --card2: #1a1a2e;
    --accent: #e94560;
    --gold: #f5a623;
    --green: #2ecc71;
    --text: #eaeaea;
    --text-muted: #8a9bb4;
    --border: #2a2a4a;
}

* { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: var(--bg); color: var(--text); }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1b2a 0%, #16213e 100%);
    border-right: 1px solid var(--border);
}

.sidebar-logo {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: var(--text);
    padding: 1rem 0 0.2rem 0;
    text-align: center;
}
.sidebar-logo span { color: var(--accent); }
.sidebar-tagline {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.75rem;
    margin-bottom: 1.5rem;
}

.page-header { margin-bottom: 1.5rem; }
.page-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.8rem;
    color: var(--text);
    margin-bottom: 0.2rem;
}
.page-subtitle { color: var(--text-muted); font-size: 0.9rem; }

.docflow-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem;
    margin-bottom: 0.8rem;
}

.metric-card {
    background: var(--card2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem;
    text-align: center;
    margin-bottom: 1rem;
}
.metric-icon { font-size: 1.5rem; margin-bottom: 0.3rem; }
.metric-value { font-size: 2rem; font-weight: 700; color: var(--accent); }
.metric-label { font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem; }

div[data-testid="stButton"] > button {
    background: var(--card);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 6px;
    transition: all 0.2s;
}
div[data-testid="stButton"] > button:hover {
    border-color: var(--accent);
    color: var(--accent);
}

div[data-testid="stTabs"] [data-baseweb="tab"] {
    color: var(--text-muted);
}
div[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--accent);
    border-bottom-color: var(--accent);
}

div[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 6px; }
.stTextInput input, .stSelectbox select, .stTextArea textarea {
    background: var(--card) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
}
.stSlider [data-baseweb="slider"] { color: var(--accent); }
div[data-testid="stMetric"] { background: var(--card2); border-radius: 8px; padding: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">Doc<span>Flow</span></div>
    <div class="sidebar-tagline">Assistant Bureautique Intelligent</div>
    """, unsafe_allow_html=True)

    nav_items = [
        ("dashboard",   T["nav_dashboard"]),
        ("sources",     T["nav_sources"]),
        ("analysis",    T["nav_analysis"]),
        ("generation",  T["nav_generation"]),
        ("conversion",  T["nav_conversion"]),
        ("cleaning",    T["nav_cleaning"]),
        ("templates",   T["nav_templates"]),
    ]

    for page_id, label in nav_items:
        is_active = st.session_state["current_page"] == page_id
        if is_active:
            st.markdown(f"""
            <div style="background:rgba(233,69,96,0.15); border-left:3px solid #e94560;
                        padding:0.6rem 1rem; border-radius:0 6px 6px 0; margin-bottom:0.3rem;
                        color:#e94560; font-weight:600;">
                {label}
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(label, key=f"nav_{page_id}", use_container_width=True):
                st.session_state["current_page"] = page_id
                st.session_state.pop("selected_conv", None)
                st.session_state.pop("selected_template", None)
                st.session_state.pop("analysis_done", None)
                st.session_state.pop("clean_result", None)
                st.session_state.pop("gen_result", None)
                st.session_state.pop("conv_result", None)
                st.rerun()

    st.markdown("---")
    if st.button(T["lang_toggle"], key="lang_toggle", use_container_width=True):
        st.session_state["lang"] = "en" if st.session_state["lang"] == "fr" else "fr"
        st.rerun()

    st.markdown(f"""
    <div style="text-align:center; color:var(--text-muted); font-size:0.7rem; margin-top:2rem;">
        DocFlow v1.0.0<br>Molo Molo Pay
    </div>
    """, unsafe_allow_html=True)

# Routing
from app.pages import (
    dashboard, data_sources, data_analysis,
    document_generation, document_conversion,
    data_cleaning, templates,
)

page = st.session_state["current_page"]
user_id = st.session_state["user_id"]

if page == "dashboard":
    dashboard.render(T, user_id)
elif page == "sources":
    data_sources.render(T, user_id)
elif page == "analysis":
    data_analysis.render(T, user_id)
elif page == "generation":
    document_generation.render(T, user_id)
elif page == "conversion":
    document_conversion.render(T, user_id)
elif page == "cleaning":
    data_cleaning.render(T, user_id)
elif page == "templates":
    templates.render(T, user_id)
