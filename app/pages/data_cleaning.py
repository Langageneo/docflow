"""
Page: Nettoyage des données
"""

import streamlit as st
import pandas as pd
import io
from app.database.db import get_user_files
from app.utils.data_utils import clean_dataframe


def render(T, user_id):
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">{T['clean_title']}</div>
        <div class="page-subtitle">{T['clean_subtitle']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Bouton retour dashboard
    if st.button(T["btn_back"], key="clean_back"):
        st.session_state["current_page"] = "dashboard"
        st.session_state.pop("clean_df", None)
        st.session_state.pop("clean_result", None)
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Si résultat disponible, bouton retour à la sélection
    if st.session_state.get("clean_result"):
        if st.button("← Nettoyer un autre fichier", key="clean_new"):
            st.session_state.pop("clean_df", None)
            st.session_state.pop("clean_result", None)
            st.rerun()
        _render_results(T)
        return

    # Sélection fichier
    df = st.session_state.get("current_df")
    file_name = st.session_state.get("current_file_name", "fichier")
    files = get_user_files(user_id)

    if df is None:
        if files:
            st.markdown(f"### {T['clean_select']}")
            options = {f["id"]: f["original_name"] for f in files}
            selected_id = st.selectbox("", list(options.keys()),
                                        format_func=lambda x: options[x], key="clean_file_select")
            if st.button("📂 Charger", key="clean_load", use_container_width=True):
                selected_file = next(f for f in files if f["id"] == selected_id)
                try:
                    if selected_file["file_path"].endswith(".csv"):
                        df = pd.read_csv(selected_file["file_path"])
                    else:
                        df = pd.read_excel(selected_file["file_path"])
                    st.session_state["current_df"] = df
                    st.session_state["current_file_name"] = selected_file["original_name"]
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
        else:
            st.markdown(f"""
            <div class="docflow-card" style="text-align:center; padding:3rem;">
                <div style="font-size:3rem;">📂</div>
                <div style="color:var(--text-muted); margin-top:1rem;">Aucun fichier disponible</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📂 Importer un fichier", key="clean_goto_sources"):
                st.session_state["current_page"] = "sources"
                st.rerun()
        return

    st.info(f"📄 Fichier actif : **{file_name}** — {len(df):,} lignes × {len(df.columns)} colonnes")

    if st.button("📂 Changer de fichier", key="clean_change"):
        st.session_state.pop("current_df", None)
        st.rerun()

    # Analyse des problèmes
    missing = df.isnull().sum().sum()
    dupes = df.duplicated().sum()
    missing_pct = missing / (len(df) * len(df.columns)) * 100 if len(df) > 0 else 0

    st.markdown("### 🔍 Problèmes détectés")
    c1, c2, c3 = st.columns(3)
    with c1:
        color = "#e94560" if missing > 0 else "#2ecc71"
        st.markdown(f"""
        <div class="metric-card" style="border-left: 3px solid {color};">
            <div class="metric-icon">❓</div>
            <div class="metric-value">{missing:,}</div>
            <div class="metric-label">Valeurs manquantes ({missing_pct:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        color = "#e94560" if dupes > 0 else "#2ecc71"
        st.markdown(f"""
        <div class="metric-card" style="border-left: 3px solid {color};">
            <div class="metric-icon">🔁</div>
            <div class="metric-value">{dupes:,}</div>
            <div class="metric-label">Doublons</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📐</div>
            <div class="metric-value">{len(df.columns)}</div>
            <div class="metric-label">Colonnes</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### ⚙️ Options de nettoyage")
    col_opts, col_preview = st.columns([1, 1])

    with col_opts:
        remove_dupes = st.checkbox(T["clean_duplicates"], value=dupes > 0, key="clean_opt_dupes")
        fill_missing = st.checkbox(T["clean_missing"], value=missing > 0, key="clean_opt_missing")
        if fill_missing:
            fill_method = st.selectbox(T["clean_method"],
                                        ["mean", "median", "zero", "drop"],
                                        format_func=lambda x: {
                                            "mean": "Moyenne", "median": "Médiane",
                                            "zero": "Zéro", "drop": "Supprimer les lignes"
                                        }[x], key="clean_fill_method")
        else:
            fill_method = "mean"
        normalize_cols = st.checkbox(T["clean_normalize"], value=False, key="clean_opt_normalize")
        fix_formats = st.checkbox(T["clean_formats"], value=False, key="clean_opt_formats")

        if st.button(T["clean_apply"], key="clean_apply_btn", use_container_width=True):
            with st.spinner(T["msg_processing"]):
                options = {
                    "remove_duplicates": remove_dupes,
                    "fill_missing": fill_missing,
                    "fill_method": fill_method,
                    "normalize_columns": normalize_cols,
                    "fix_formats": fix_formats,
                }
                df_clean, report = clean_dataframe(df, options)
                st.session_state["clean_df"] = df_clean
                st.session_state["clean_result"] = report
                st.session_state["clean_file_name"] = file_name
            st.rerun()

    with col_preview:
        st.markdown("#### Aperçu des données")
        st.dataframe(df.head(10), use_container_width=True)


def _render_results(T):
    df_clean = st.session_state.get("clean_df")
    report = st.session_state.get("clean_result", {})
    file_name = st.session_state.get("clean_file_name", "fichier_nettoye")
    lang = st.session_state.get("lang", "fr")

    st.markdown("### ✅ Résultats du nettoyage")

    orig = report.get("original_shape", (0, 0))
    final = report.get("final_shape", (0, 0))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">🗑️</div>
            <div class="metric-value">{report.get('duplicates_removed', 0)}</div>
            <div class="metric-label">Doublons supprimés</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{report.get('missing_filled', 0)}</div>
            <div class="metric-label">Valeurs remplies</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">📏</div>
            <div class="metric-value">{report.get('rows_removed', 0)}</div>
            <div class="metric-label">Lignes supprimées</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-icon">📐</div>
            <div class="metric-value">{final[0]:,}</div>
            <div class="metric-label">Lignes finales</div>
        </div>""", unsafe_allow_html=True)

    if df_clean is not None:
        st.markdown("#### Aperçu des données nettoyées")
        st.dataframe(df_clean.head(20), use_container_width=True)

        col1, col2, col3 = st.columns(3)
        base = file_name.replace(".csv", "").replace(".xlsx", "") + "_nettoye"

        with col1:
            csv_data = df_clean.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ CSV", csv_data, f"{base}.csv",
                               "text/csv", use_container_width=True, key="clean_dl_csv")
        with col2:
            from app.utils.doc_generator import generate_excel_report
            xlsx = generate_excel_report(df_clean, base, lang=lang)
            st.download_button("⬇️ Excel", xlsx, f"{base}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True, key="clean_dl_xlsx")
        with col3:
            if st.button("📊 Analyser les données nettoyées", use_container_width=True, key="clean_goto_analysis"):
                st.session_state["current_df"] = df_clean
                st.session_state["current_file_name"] = base
                st.session_state["current_page"] = "analysis"
                st.rerun()
