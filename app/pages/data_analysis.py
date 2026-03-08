"""
Page: Analyse des données
"""

import streamlit as st
import pandas as pd
from app.database.db import get_user_files, save_analysis
from app.utils.data_utils import compute_statistics, generate_insights
from app.utils.chart_utils import auto_chart
import json


def render(T, user_id):
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">{T['analysis_title']}</div>
        <div class="page-subtitle">{T['analysis_subtitle']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Bouton retour toujours visible
    if st.button(T["btn_back"], key="analysis_back"):
        st.session_state["current_page"] = "dashboard"
        st.session_state.pop("analysis_done", None)
        st.session_state.pop("analysis_stats", None)
        st.session_state.pop("analysis_insights", None)
        st.session_state.pop("analysis_charts", None)
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Si analyse déjà faite, afficher résultats avec bouton retour à la sélection
    if st.session_state.get("analysis_done"):
        if st.button("← Nouvelle analyse", key="analysis_new"):
            st.session_state.pop("analysis_done", None)
            st.session_state.pop("analysis_stats", None)
            st.session_state.pop("analysis_insights", None)
            st.session_state.pop("analysis_charts", None)
            st.rerun()
        _render_results(T, user_id)
        return

    # Sélection du fichier
    files = get_user_files(user_id)
    current_df = st.session_state.get("current_df")
    current_name = st.session_state.get("current_file_name", "")

    if current_df is not None:
        st.info(f"📄 Fichier actif : **{current_name}** — {len(current_df):,} lignes × {len(current_df.columns)} colonnes")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(T["analysis_run"], key="run_analysis_current", use_container_width=True):
                _run_analysis(T, user_id, current_df, current_name)
        with col2:
            if st.button("📂 Choisir un autre fichier", key="analysis_change_file", use_container_width=True):
                st.session_state.pop("current_df", None)
                st.rerun()
    elif files:
        st.markdown(f"### {T['analysis_select']}")
        options = {f["id"]: f["original_name"] for f in files}
        selected_id = st.selectbox("", list(options.keys()),
                                    format_func=lambda x: options[x], key="analysis_file_select")
        if st.button(T["analysis_run"], key="run_analysis_select", use_container_width=True):
            selected_file = next(f for f in files if f["id"] == selected_id)
            try:
                if selected_file["file_path"].endswith(".csv"):
                    df = pd.read_csv(selected_file["file_path"])
                else:
                    df = pd.read_excel(selected_file["file_path"])
                _run_analysis(T, user_id, df, selected_file["original_name"])
            except Exception as e:
                st.error(f"❌ Erreur: {e}")
    else:
        st.markdown(f"""
        <div class="docflow-card" style="text-align:center; padding:3rem;">
            <div style="font-size:3rem;">📂</div>
            <div style="color:var(--text-muted); margin-top:1rem;">Aucun fichier disponible</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📂 Importer un fichier", key="analysis_goto_sources"):
            st.session_state["current_page"] = "sources"
            st.rerun()


def _run_analysis(T, user_id, df, file_name):
    with st.spinner(T["msg_processing"]):
        lang = st.session_state.get("lang", "fr")
        stats = compute_statistics(df)
        insights = generate_insights(df, lang=lang)
        charts = auto_chart(df, lang=lang)
        st.session_state["analysis_done"] = True
        st.session_state["analysis_df"] = df
        st.session_state["analysis_stats"] = stats
        st.session_state["analysis_insights"] = insights
        st.session_state["analysis_charts"] = charts
        st.session_state["analysis_file_name"] = file_name
        file_id = st.session_state.get("current_file_id", 1)
        save_analysis(user_id, file_id, json.dumps(stats, default=str),
                      "\n".join(insights), len(charts))
    st.rerun()


def _render_results(T, user_id):
    df = st.session_state.get("analysis_df")
    stats = st.session_state.get("analysis_stats", {})
    insights = st.session_state.get("analysis_insights", [])
    charts = st.session_state.get("analysis_charts", [])
    file_name = st.session_state.get("analysis_file_name", "")

    st.markdown(f"### 📄 {file_name}")

    # Métriques
    shape = stats.get("shape", {})
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">📏</div>
            <div class="metric-value">{shape.get('rows', 0):,}</div>
            <div class="metric-label">{T['analysis_rows']}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">📐</div>
            <div class="metric-value">{shape.get('cols', 0)}</div>
            <div class="metric-label">{T['analysis_cols']}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">❓</div>
            <div class="metric-value">{stats.get('missing', 0):,}</div>
            <div class="metric-label">{T['analysis_missing']}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">🔁</div>
            <div class="metric-value">{stats.get('duplicates', 0):,}</div>
            <div class="metric-label">{T['analysis_duplicates']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        T["analysis_stats"], T["analysis_charts"],
        T["analysis_insights"], T["analysis_export"]
    ])

    with tab1:
        if df is not None:
            st.markdown("#### Aperçu des données")
            st.dataframe(df.head(20), use_container_width=True)
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if numeric_cols:
                st.markdown("#### Statistiques descriptives")
                st.dataframe(df[numeric_cols].describe().round(2), use_container_width=True)

    with tab2:
        if charts:
            for chart_id, fig in charts:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun graphique disponible pour ces données.")

    with tab3:
        for insight in insights:
            st.markdown(f"""
            <div class="docflow-card" style="padding:0.8rem 1.2rem; margin-bottom:0.5rem;">
                {insight}
            </div>
            """, unsafe_allow_html=True)

    with tab4:
        if df is not None:
            lang = st.session_state.get("lang", "fr")
            col1, col2, col3 = st.columns(3)
            with col1:
                from app.utils.doc_generator import generate_excel_report
                xlsx = generate_excel_report(df, file_name, lang=lang)
                st.download_button("📊 Excel", xlsx, f"{file_name}.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True, key="analysis_dl_excel")
            with col2:
                from app.utils.doc_generator import generate_pdf_report
                pdf = generate_pdf_report(df, file_name, lang=lang)
                st.download_button("📕 PDF", pdf, f"{file_name}.pdf",
                                   "application/pdf", use_container_width=True, key="analysis_dl_pdf")
            with col3:
                from app.utils.doc_generator import generate_word_report
                docx = generate_word_report(df, file_name, lang=lang)
                st.download_button("📝 Word", docx, f"{file_name}.docx",
                                   "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   use_container_width=True, key="analysis_dl_word")
