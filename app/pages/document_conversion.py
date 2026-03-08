"""
Page: Conversion de documents
"""

import streamlit as st
import pandas as pd
import io
import os
from app.database.db import save_conversion
from app.utils import sheets_utils


def render(T, user_id):
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">{T['conv_title']}</div>
        <div class="page-subtitle">{T['conv_subtitle']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Bouton retour dashboard
    if st.button(T["btn_back"], key="conv_back_dash"):
        st.session_state["current_page"] = "dashboard"
        st.session_state.pop("selected_conv", None)
        st.session_state.pop("conv_result", None)
        st.rerun()

    CONVERSIONS = [
        ("csv_to_excel", T["conv_csv_to_excel"], ["csv"], "xlsx", "📊"),
        ("excel_to_pdf", T["conv_excel_to_pdf"], ["xlsx", "xls"], "pdf", "📕"),
        ("excel_to_word", T["conv_excel_to_word"], ["xlsx", "xls"], "docx", "📝"),
        ("pdf_to_excel", T["conv_pdf_to_excel"], ["pdf"], "xlsx", "📊"),
        ("word_to_pdf", T["conv_word_to_pdf"], ["docx"], "pdf", "📕"),
        ("any_to_sheets", "Fichier → Google Sheets", ["xlsx", "xls", "csv"], "gsheets", "🟢"),
    ]

    selected = st.session_state.get("selected_conv")

    if not selected:
        st.markdown("### Choisissez un type de conversion")
        cols = st.columns(3)
        for i, (conv_id, label, from_fmts, to_fmt, icon) in enumerate(CONVERSIONS):
            with cols[i % 3]:
                if st.button(f"{icon} {label}", key=f"conv_sel_{conv_id}", use_container_width=True):
                    st.session_state["selected_conv"] = conv_id
                    st.rerun()
        return

    conv_info = next((c for c in CONVERSIONS if c[0] == selected), None)
    if not conv_info:
        return

    conv_id, label, from_fmts, to_fmt, icon = conv_info

    # Bouton retour vers liste conversions
    if st.button("← Retour aux conversions", key="conv_back_list"):
        st.session_state.pop("selected_conv", None)
        st.session_state.pop("conv_result", None)
        st.session_state.pop("conv_sheets_result", None)
        st.rerun()

    st.markdown(f"### {icon} {label}")
    st.markdown("---")

    if conv_id == "any_to_sheets":
        _render_sheets_conversion(T, user_id, from_fmts)
        return

    col_upload, col_result = st.columns([1, 1])

    with col_upload:
        uploaded = st.file_uploader(T["conv_upload"], type=from_fmts, key=f"conv_upload_{conv_id}")
        if uploaded and st.button(f"🔄 {T['conv_btn']}", use_container_width=True, key="do_convert"):
            with st.spinner(T["msg_processing"]):
                try:
                    result_data, result_name, mime = _do_convert(uploaded, conv_id)
                    st.session_state["conv_result"] = {
                        "data": result_data, "fname": result_name, "mime": mime
                    }
                    save_conversion(user_id, uploaded.name, uploaded.name.split(".")[-1], to_fmt, result_name, "done")
                    st.success(f"✅ {T['conv_success']}")
                except Exception as e:
                    st.error(f"❌ {e}")

    with col_result:
        if "conv_result" in st.session_state:
            r = st.session_state["conv_result"]
            st.markdown(f"""
            <div class="docflow-card" style="text-align:center; padding:2rem;">
                <div style="font-size:3rem;">{icon}</div>
                <div style="color:var(--text); font-weight:600; margin:1rem 0 0.5rem;">{r['fname']}</div>
                <div style="color:var(--text-muted);">{len(r['data'])/1024:.1f} Ko</div>
            </div>
            """, unsafe_allow_html=True)
            st.download_button(f"⬇️ {T['conv_download']}", r["data"], r["fname"],
                               r["mime"], use_container_width=True, key="dl_conv_result")
        else:
            st.markdown(f"""
            <div class="docflow-card" style="text-align:center; padding:4rem 2rem;">
                <div style="font-size:3rem; opacity:0.3;">{icon}</div>
                <div style="color:var(--text-muted); margin-top:1rem;">Votre fichier converti apparaîtra ici</div>
            </div>
            """, unsafe_allow_html=True)


def _render_sheets_conversion(T, user_id, from_fmts):
    if not sheets_utils.is_configured():
        st.error("⚠️ credentials.json introuvable.")
        return

    st.success("✅ Google API configurée")
    col_left, col_right = st.columns([1, 1])

    with col_left:
        uploaded = st.file_uploader("Fichier à convertir", type=from_fmts, key="sheets_conv_upload")
        sheets_name = st.text_input("Nom du fichier Sheets", value="Conversion DocFlow", key="conv_sheets_name")
        share_email = st.text_input("Partager avec (email Gmail)", placeholder="collegue@gmail.com", key="conv_sheets_email")
        if uploaded and st.button("🚀 Envoyer vers Google Sheets", use_container_width=True, key="do_conv_sheets"):
            with st.spinner(T["msg_processing"]):
                try:
                    content = uploaded.read()
                    lang = st.session_state.get("lang", "fr")
                    ext = uploaded.name.split(".")[-1].lower()
                    if ext == "csv":
                        result = sheets_utils.export_csv_to_sheets(content, sheets_name,
                            share_email=share_email if share_email.strip() else None, lang=lang)
                    else:
                        result = sheets_utils.export_excel_to_sheets(content, sheets_name,
                            share_email=share_email if share_email.strip() else None, lang=lang)
                    save_conversion(user_id, uploaded.name, ext, "gsheets", result["url"], "done")
                    st.session_state["conv_sheets_result"] = result
                    st.success("✅ Google Sheets créé avec succès !")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")

    with col_right:
        if "conv_sheets_result" in st.session_state:
            result = st.session_state["conv_sheets_result"]
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
        else:
            st.markdown(f"""
            <div class="docflow-card" style="text-align:center; padding:4rem 2rem;">
                <div style="font-size:3rem; opacity:0.3;">🟢</div>
                <div style="color:var(--text-muted); margin-top:1rem;">Votre Google Sheets apparaîtra ici</div>
            </div>
            """, unsafe_allow_html=True)


def _do_convert(uploaded, conv_id):
    content = uploaded.read()
    base_name = os.path.splitext(uploaded.name)[0]

    if conv_id == "csv_to_excel":
        df = pd.read_csv(io.BytesIO(content))
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Données")
        return output.getvalue(), f"{base_name}.xlsx", \
               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    elif conv_id == "excel_to_pdf":
        df = pd.read_excel(io.BytesIO(content))
        from app.utils.doc_generator import generate_pdf_report
        lang = st.session_state.get("lang", "fr")
        return generate_pdf_report(df, base_name, lang=lang), f"{base_name}.pdf", "application/pdf"

    elif conv_id == "excel_to_word":
        df = pd.read_excel(io.BytesIO(content))
        from app.utils.doc_generator import generate_word_report
        lang = st.session_state.get("lang", "fr")
        return generate_word_report(df, base_name, lang=lang), f"{base_name}.docx", \
               "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    elif conv_id == "word_to_pdf":
        from docx import Document as DocxDoc
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        doc = DocxDoc(io.BytesIO(content))
        output = io.BytesIO()
        pdf_doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        for para in doc.paragraphs:
            if para.text.strip():
                story.append(Paragraph(para.text, styles["Normal"]))
                story.append(Spacer(1, 6))
        pdf_doc.build(story)
        return output.getvalue(), f"{base_name}.pdf", "application/pdf"

    elif conv_id == "pdf_to_excel":
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                tables = []
                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        tables.extend(table)
            if tables:
                df = pd.DataFrame(tables[1:], columns=tables[0])
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False)
                return output.getvalue(), f"{base_name}.xlsx", \
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                raise ValueError("Aucun tableau trouvé dans le PDF")
        except ImportError:
            raise ValueError("pdfplumber non installé")

    raise ValueError(f"Conversion non supportée: {conv_id}")
