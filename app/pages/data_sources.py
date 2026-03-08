"""
Page: Sources de données
"""

import streamlit as st
import pandas as pd
import io
from app.database.db import save_file_record, get_user_files, delete_file_record, get_file_by_id
from app.utils.data_utils import save_uploaded_file, format_file_size


def render(T, user_id):
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">{T['src_title']}</div>
        <div class="page-subtitle">{T['src_subtitle']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Bouton retour
    if st.button(T["btn_back"], key="src_back"):
        st.session_state["current_page"] = "dashboard"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([T["src_upload"], T["src_sheets"], T["src_paste"]])

    with tab1:
        _render_upload(T, user_id)

    with tab2:
        _render_sheets(T, user_id)

    with tab3:
        _render_paste(T, user_id)

    st.markdown("---")
    _render_file_list(T, user_id)


def _render_upload(T, user_id):
    st.markdown("<br>", unsafe_allow_html=True)
    uploaded = st.file_uploader(
        T["src_upload_label"],
        type=["csv", "xlsx", "xls"],
        key="src_file_uploader"
    )
    if uploaded:
        try:
            with st.spinner(T["msg_processing"]):
                stored_name, file_path = save_uploaded_file(uploaded)
                if uploaded.name.endswith(".csv"):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                file_id = save_file_record(
                    user_id, uploaded.name, stored_name, file_path,
                    uploaded.name.split(".")[-1].upper(),
                    uploaded.size, len(df), len(df.columns)
                )
                st.session_state["current_df"] = df
                st.session_state["current_file_id"] = file_id
                st.session_state["current_file_name"] = uploaded.name
            st.success(f"✅ {T['src_success']} — {len(df):,} lignes × {len(df.columns)} colonnes")
            st.dataframe(df.head(10), use_container_width=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 " + T["nav_analysis"] if "nav_analysis" in T else "📊 Analyser",
                             key="src_goto_analysis", use_container_width=True):
                    st.session_state["current_page"] = "analysis"
                    st.rerun()
            with col2:
                if st.button("📝 Générer un rapport", key="src_goto_gen", use_container_width=True):
                    st.session_state["current_page"] = "generation"
                    st.rerun()
        except Exception as e:
            st.error(f"❌ {T['src_error']}: {e}")


def _render_sheets(T, user_id):
    from app.utils import sheets_utils
    st.markdown("<br>", unsafe_allow_html=True)
    if not sheets_utils.is_configured():
        st.warning("⚠️ Google Sheets API non configurée. Placez votre credentials.json dans le dossier du projet.")
        return
    st.success("✅ Google API configurée")
    sheet_url = st.text_input("URL Google Sheets", placeholder="https://docs.google.com/spreadsheets/d/...")
    if sheet_url and st.button("📥 Importer", key="src_import_sheets"):
        try:
            with st.spinner(T["msg_processing"]):
                client = sheets_utils.get_client()
                spreadsheet = client.open_by_url(sheet_url)
                ws = spreadsheet.sheet1
                data = ws.get_all_records()
                df = pd.DataFrame(data)
                import os, hashlib
                from datetime import datetime
                from app.config import Config
                os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                stored_name = f"{ts}_sheets.csv"
                file_path = os.path.join(Config.UPLOAD_DIR, stored_name)
                df.to_csv(file_path, index=False)
                file_id = save_file_record(user_id, spreadsheet.title + ".csv", stored_name,
                                           file_path, "CSV", 0, len(df), len(df.columns))
                st.session_state["current_df"] = df
                st.session_state["current_file_id"] = file_id
                st.session_state["current_file_name"] = spreadsheet.title
            st.success(f"✅ {len(df):,} lignes importées depuis Google Sheets")
            st.dataframe(df.head(10), use_container_width=True)
        except Exception as e:
            st.error(f"❌ Erreur: {e}")


def _render_paste(T, user_id):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("Collez vos données CSV ou tabulaires ci-dessous :")
    pasted = st.text_area("Données", height=200, placeholder="col1,col2,col3\nval1,val2,val3", key="src_paste_area")
    sep = st.radio("Séparateur", [",", ";", "\\t"], horizontal=True, key="src_sep")
    if pasted and st.button("📥 Charger", key="src_load_paste"):
        try:
            actual_sep = "\t" if sep == "\\t" else sep
            df = pd.read_csv(io.StringIO(pasted), sep=actual_sep)
            import os
            from datetime import datetime
            from app.config import Config
            os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            stored_name = f"{ts}_paste.csv"
            file_path = os.path.join(Config.UPLOAD_DIR, stored_name)
            df.to_csv(file_path, index=False)
            file_id = save_file_record(user_id, "donnees_collees.csv", stored_name,
                                       file_path, "CSV", len(pasted), len(df), len(df.columns))
            st.session_state["current_df"] = df
            st.session_state["current_file_id"] = file_id
            st.session_state["current_file_name"] = "donnees_collees.csv"
            st.success(f"✅ {len(df):,} lignes chargées")
            st.dataframe(df.head(10), use_container_width=True)
        except Exception as e:
            st.error(f"❌ Erreur: {e}")


def _render_file_list(T, user_id):
    st.markdown(f"### {T['src_my_files']}")
    files = get_user_files(user_id)
    if not files:
        st.info(T["src_no_files"])
        return
    for f in files:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.markdown(f"""
            <div style="padding:0.4rem 0;">
                <span style="color:#e94560;">📄</span>
                <span style="color:var(--text); margin-left:0.4rem;">{f['original_name']}</span>
                <span style="color:var(--text-muted); margin-left:0.5rem; font-size:0.8rem;">
                    {f['row_count']:,} lignes · {f['col_count']} cols · {f['uploaded_at'][:10]}
                </span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("📊", key=f"fl_analyze_{f['id']}", help="Analyser"):
                import pandas as pd
                try:
                    if f["file_path"].endswith(".csv"):
                        df = pd.read_csv(f["file_path"])
                    else:
                        df = pd.read_excel(f["file_path"])
                    st.session_state["current_df"] = df
                    st.session_state["current_file_id"] = f["id"]
                    st.session_state["current_file_name"] = f["original_name"]
                    st.session_state["current_page"] = "analysis"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
        with col3:
            if st.button("📝", key=f"fl_gen_{f['id']}", help="Générer"):
                import pandas as pd
                try:
                    if f["file_path"].endswith(".csv"):
                        df = pd.read_csv(f["file_path"])
                    else:
                        df = pd.read_excel(f["file_path"])
                    st.session_state["current_df"] = df
                    st.session_state["current_file_id"] = f["id"]
                    st.session_state["current_file_name"] = f["original_name"]
                    st.session_state["current_page"] = "generation"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
        with col4:
            if st.button("🗑️", key=f"fl_del_{f['id']}", help="Supprimer"):
                delete_file_record(f["id"], user_id)
                st.rerun()
