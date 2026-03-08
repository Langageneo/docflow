"""
Page: Tableau de bord
"""

import streamlit as st
from app.database.db import get_user_stats, get_user_files, get_user_reports


def render(T, user_id):
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">{T['dash_welcome']}</div>
        <div class="page-subtitle">{T['dash_subtitle']}</div>
    </div>
    """, unsafe_allow_html=True)

    stats = get_user_stats(user_id)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📂</div>
            <div class="metric-value">{stats['files']}</div>
            <div class="metric-label">{T['dash_files']}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📝</div>
            <div class="metric-value">{stats['reports']}</div>
            <div class="metric-label">{T['dash_reports']}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-value">{stats['analyses']}</div>
            <div class="metric-label">{T['dash_analyses']}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🔄</div>
            <div class="metric-value">{stats['conversions']}</div>
            <div class="metric-label">{T['dash_conversions']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown(f"### {T['dash_quick_start']}")
        actions = [
            ("📂", T['nav_sources'], "sources"),
            ("📊", T['nav_analysis'], "analysis"),
            ("📝", T['nav_generation'], "generation"),
            ("🔄", T['nav_conversion'], "conversion"),
            ("🧹", T['nav_cleaning'], "cleaning"),
            ("📋", T['nav_templates'], "templates"),
        ]
        cols = st.columns(2)
        for i, (icon, label, page) in enumerate(actions):
            with cols[i % 2]:
                if st.button(f"{icon} {label}", key=f"dash_nav_{page}", use_container_width=True):
                    st.session_state["current_page"] = page
                    st.rerun()

    with col_right:
        st.markdown(f"### {T['dash_recent']}")
        files = get_user_files(user_id)
        if files:
            for f in files[:5]:
                st.markdown(f"""
                <div class="docflow-card" style="padding:0.6rem 1rem; margin-bottom:0.4rem;">
                    <span style="color:#e94560;">📄</span>
                    <span style="color:var(--text); margin-left:0.5rem;">{f['original_name']}</span>
                    <span style="color:var(--text-muted); float:right; font-size:0.75rem;">{f['uploaded_at'][:10]}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="docflow-card" style="text-align:center; padding:2rem; color:var(--text-muted);">
                {T['msg_no_data']}
            </div>
            """, unsafe_allow_html=True)
