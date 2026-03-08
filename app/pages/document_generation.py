"""
Page: Génération de documents
"""

import streamlit as st
import pandas as pd
from app.database.db import get_user_files, save_report
from app.utils.doc_generator import generate_excel_report, generate_pdf_report, generate_word_report
from app.utils import sheets_utils


def render(T, user_id):
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">{T['gen_title']}</div>
        <div class="page-subtitle">{T['gen_subtitle']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Bouton retour
    if st.button(T["btn_back"], key="gen_back"):
        st.session_state["current_page"] = "dashboard"
        st.session_state.pop("gen_result", None)
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Sélection du fichier
    df = st.session_state.get("current_df")
    file_name = st.session_state.get("current_file_name", "rapport")
    files = get_user_files(user_id)

    if df is None:
        if files:
            st.markdown(f"### {T['gen_select_file']}")
            options = {f["id"]: f["original_name"] for f in files}
            selected_id = st.selectbox("", list(options.keys()),
                                        format_func=lambda x: options[x], key="gen_file_select")
            if st.button("📂 Charger", key="gen_load_file", use_container_width=True):
                selected_file = next(f for f in files if f["id"] == selected_id)
                try:
                    if selected_file["file_path"].endswith(".csv"):
                        df = pd.read_csv(selected_file["file_path"])
                    else:
                        df = pd.read_excel(selected_file["file_path"])
                    st.session_state["current_df"] = df
                    st.session_state["current_file_id"] = selected_file["id"]
                    st.session_state["current_file_name"] = selected_file["original_name"]
                    file_name = selected_file["original_name"]
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
            return
        else:
            st.markdown(f"""
            <div class="docflow-card" style="text-align:center; padding:3rem;">
                <div style="font-size:3rem;">📂</div>
                <div style="color:var(--text-muted); margin-top:1rem;">Aucun fichier disponible</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📂 Importer un fichier", key="gen_goto_sources"):
                st.session_state["current_page"] = "sources"
                st.rerun()
            return

    st.info(f"📄 Fichier actif : **{file_name}** — {len(df):,} lignes × {len(df.columns)} colonnes")

    if st.button("📂 Changer de fichier", key="gen_change_file"):
        st.session_state.pop("current_df", None)
        st.session_state.pop("gen_result", None)
        st.rerun()

    st.markdown("---")

    lang = st.session_state.get("lang", "fr")

    col_opts, col_result = st.columns([1, 1])

    with col_opts:
        report_title = st.text_input(T["gen_report_title"],
                                      value=file_name.replace(".csv", "").replace(".xlsx", ""),
                                      key="gen_title_input")
        company = st.text_input(T["gen_company"], value="Mon Entreprise", key="gen_company_input")

        st.markdown("#### Choisissez le format")
        tab1, tab2, tab3, tab4 = st.tabs([T["gen_excel"], T["gen_pdf"], T["gen_word"], T["gen_sheets"]])

        with tab1:
            st.markdown("Rapport Excel avec statistiques et mise en forme professionnelle.")
            if st.button(f"📊 {T['gen_generate']}", key="gen_excel_btn", use_container_width=True):
                with st.spinner(T["msg_processing"]):
                    try:
                        data = generate_excel_report(df, report_title, company=company, lang=lang)
                        fname = f"{report_title}.xlsx"
                        st.session_state["gen_result"] = {"data": data, "fname": fname,
                                                           "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                                           "type": "excel"}
                        save_report(user_id, report_title, "xlsx", fname)
                        st.success(f"✅ {T['gen_success']}")
                    except Exception as e:
                        st.error(f"❌ {e}")

        with tab2:
            st.markdown("Rapport PDF avec tableaux, statistiques et mise en page professionnelle.")
            if st.button(f"📕 {T['gen_generate']}", key="gen_pdf_btn", use_container_width=True):
                with st.spinner(T["msg_processing"]):
                    try:
                        data = generate_pdf_report(df, report_title, lang=lang)
                        fname = f"{report_title}.pdf"
                        st.session_state["gen_result"] = {"data": data, "fname": fname,
                                                           "mime": "application/pdf", "type": "pdf"}
                        save_report(user_id, report_title, "pdf", fname)
                        st.success(f"✅ {T['gen_success']}")
                    except Exception as e:
                        st.error(f"❌ {e}")

        with tab3:
            st.markdown("Rapport Word avec tableaux et statistiques formatés.")
            if st.button(f"📝 {T['gen_generate']}", key="gen_word_btn", use_container_width=True):
                with st.spinner(T["msg_processing"]):
                    try:
                        data = generate_word_report(df, report_title, lang=lang)
                        fname = f"{report_title}.docx"
                        st.session_state["gen_result"] = {"data": data, "fname": fname,
                                                           "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                                           "type": "word"}
                        save_report(user_id, report_title, "docx", fname)
                        st.success(f"✅ {T['gen_success']}")
                    except Exception as e:
                        st.error(f"❌ {e}")

        with tab4:
            if not sheets_utils.is_configured():
                st.warning("⚠️ Google Sheets API non configurée.")
            else:
                st.success("✅ Google API configurée")
                share_email = st.text_input("Partager avec (email)", placeholder="collegue@gmail.com",
                                             key="gen_sheets_email")
                if st.button(f"🟢 {T['gen_generate']}", key="gen_sheets_btn", use_container_width=True):
                    with st.spinner(T["msg_processing"]):
                        try:
                            result = sheets_utils.export_dataframe_to_sheets(
                                df, report_title,
                                share_email=share_email if share_email.strip() else None,
                                lang=lang
                            )
                            st.session_state["gen_sheets_result"] = result
                            save_report(user_id, report_title, "gsheets", result["url"])
                            st.success("✅ Google Sheets créé !")
                        except Exception as e:
                            st.error(f"❌ {e}")

    with col_result:
        st.markdown("### Résultat")

        if "gen_sheets_result" in st.session_state:
            result = st.session_state["gen_sheets_result"]
            st.markdown(f"""
            <div class="docflow-card" style="text-align:center; padding:2rem;">
                <div style="font-size:4rem;">🟢</div>
                <div style="color:var(--text); font-size:1.1rem; font-weight:600; margin:1rem 0 0.5rem;">
                    {result['title']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.code(result["url"], language=None)
            st.link_button("🔗 Ouvrir dans Google Sheets", result["url"], use_container_width=True)

        elif "gen_result" in st.session_state:
            r = st.session_state["gen_result"]
            icons = {"excel": "📊", "pdf": "📕", "word": "📝"}
            icon = icons.get(r["type"], "📄")
            st.markdown(f"""
            <div class="docflow-card" style="text-align:center; padding:2rem;">
                <div style="font-size:4rem;">{icon}</div>
                <div style="color:var(--text); font-size:1.1rem; font-weight:600; margin:1rem 0 0.5rem;">
                    {r['fname']}
                </div>
                <div style="color:var(--text-muted);">{len(r['data'])/1024:.1f} Ko</div>
            </div>
            """, unsafe_allow_html=True)
            st.download_button(T["gen_download"], r["data"], r["fname"],
                               r["mime"], use_container_width=True, key="gen_dl_btn")
        else:
            st.markdown(f"""
            <div class="docflow-card" style="text-align:center; padding:4rem 2rem;">
                <div style="font-size:3rem; opacity:0.3;">📄</div>
                <div style="color:var(--text-muted); margin-top:1rem;">
                    Votre document apparaîtra ici
                </div>
            </div>
            """, unsafe_allow_html=True)
