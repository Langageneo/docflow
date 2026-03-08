"""
Page: Modèles professionnels
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime
from app.database.db import save_report

TEMPLATES = [
    {"id": "invoice", "icon": "🧾", "color": "#e94560", "key_fr": "tmpl_invoice", "key_desc_fr": "tmpl_invoice_desc"},
    {"id": "sales", "icon": "📈", "color": "#f5a623", "key_fr": "tmpl_sales", "key_desc_fr": "tmpl_sales_desc"},
    {"id": "budget", "icon": "💰", "color": "#2ecc71", "key_fr": "tmpl_budget", "key_desc_fr": "tmpl_budget_desc"},
    {"id": "inventory", "icon": "📦", "color": "#3498db", "key_fr": "tmpl_inventory", "key_desc_fr": "tmpl_inventory_desc"},
    {"id": "marketing", "icon": "📣", "color": "#9b59b6", "key_fr": "tmpl_marketing", "key_desc_fr": "tmpl_marketing_desc"},
    {"id": "hr", "icon": "👥", "color": "#1abc9c", "key_fr": "tmpl_hr", "key_desc_fr": "tmpl_hr_desc"},
]


def render(T, user_id):
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">{T['tmpl_title']}</div>
        <div class="page-subtitle">{T['tmpl_subtitle']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Bouton retour dashboard
    if st.button(T["btn_back"], key="tmpl_back_dash"):
        st.session_state["current_page"] = "dashboard"
        st.session_state.pop("selected_template", None)
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    selected = st.session_state.get("selected_template")

    if selected:
        # Bouton retour vers liste modèles
        if st.button(T["tmpl_back"], key="tmpl_back_list"):
            st.session_state.pop("selected_template", None)
            st.rerun()
        st.markdown("---")
        _render_form(T, selected, user_id)
        return

    # Grille des modèles
    cols = st.columns(3)
    for i, tmpl in enumerate(TEMPLATES):
        with cols[i % 3]:
            name = T[tmpl["key_fr"]]
            desc = T[tmpl["key_desc_fr"]]
            st.markdown(f"""
            <div class="docflow-card" style="margin-bottom:1rem; border-left:3px solid {tmpl['color']};">
                <div style="font-size:2.5rem;">{tmpl['icon']}</div>
                <div style="font-size:1rem; font-weight:600; color:var(--text); margin:0.3rem 0;">{name}</div>
                <div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:1rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button(T["tmpl_use_btn"], key=f"use_{tmpl['id']}", use_container_width=True):
                    st.session_state["selected_template"] = tmpl
                    st.rerun()
            with c2:
                empty_data = _get_empty(tmpl["id"])
                st.download_button(T["tmpl_download_btn"], empty_data,
                                   f"template_{tmpl['id']}.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key=f"dl_empty_{tmpl['id']}", use_container_width=True)


def _render_form(T, tmpl, user_id):
    lang = st.session_state.get("lang", "fr")
    st.markdown(f"### {tmpl['icon']} {T[tmpl['key_fr']]}")
    st.markdown("---")
    tid = tmpl["id"]
    if tid == "invoice": _invoice(T, user_id, lang)
    elif tid == "sales": _sales(T, user_id, lang)
    elif tid == "budget": _budget(T, user_id, lang)
    elif tid == "inventory": _inventory(T, user_id, lang)
    elif tid == "marketing": _marketing(T, user_id, lang)
    elif tid == "hr": _hr(T, user_id, lang)


def _invoice(T, user_id, lang):
    c1, c2 = st.columns(2)
    with c1:
        company_name = st.text_input("Entreprise", "Ma Société SARL", key="inv_company")
        company_addr = st.text_area("Adresse", "123 Rue de la Paix\nAbidjan", height=80, key="inv_addr")
        company_email = st.text_input("Email", "contact@masociete.ci", key="inv_email")
    with c2:
        client_name = st.text_input("Client", "Client ABC", key="inv_client")
        client_addr = st.text_area("Adresse client", "456 Avenue Houphouet\nAbidjan", height=80, key="inv_client_addr")
        invoice_num = st.text_input("N° Facture", f"FAC-{datetime.now().strftime('%Y%m%d')}-001", key="inv_num")

    n_lines = st.number_input("Nombre de lignes", min_value=1, max_value=20, value=3, key="inv_lines")
    items = []
    st.markdown("**Détail des prestations**")
    cols_header = st.columns([3, 1, 1])
    cols_header[0].markdown("**Description**")
    cols_header[1].markdown("**Quantité**")
    cols_header[2].markdown("**Prix HT**")
    for i in range(int(n_lines)):
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1: desc = st.text_input("", f"Prestation {i+1}", label_visibility="collapsed", key=f"inv_d_{i}")
        with c2: qty = st.number_input("", min_value=1, value=1, label_visibility="collapsed", key=f"inv_q_{i}")
        with c3: price = st.number_input("", min_value=0.0, value=100.0, step=10.0, label_visibility="collapsed", key=f"inv_p_{i}")
        items.append({"Description": desc, "Quantité": qty, "Prix HT": price, "Total HT": qty * price})

    tva = st.slider("TVA (%)", 0, 25, 18, key="inv_tva")
    df = pd.DataFrame(items)
    total_ht = df["Total HT"].sum()
    tva_amt = total_ht * tva / 100
    total_ttc = total_ht + tva_amt

    c1, c2, c3 = st.columns(3)
    c1.metric("Total HT", f"{total_ht:,.0f} FCFA")
    c2.metric(f"TVA ({tva}%)", f"{tva_amt:,.0f} FCFA")
    c3.metric("Total TTC", f"{total_ttc:,.0f} FCFA")

    if st.button("📄 Générer la facture", use_container_width=True, key="gen_invoice"):
        from app.utils.doc_generator import generate_excel_report
        xlsx = generate_excel_report(df, f"Facture {invoice_num}", company=company_name, author=company_email, lang=lang)
        save_report(user_id, f"Facture {invoice_num}", "xlsx", f"facture_{invoice_num}.xlsx", template_type="invoice")
        st.download_button("⬇️ Télécharger la facture", xlsx, f"facture_{invoice_num}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="dl_invoice", use_container_width=True)


def _sales(T, user_id, lang):
    n = st.slider("Nombre de mois", 1, 12, 6, key="sales_months")
    months = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
    data = []
    cols_h = st.columns(3)
    cols_h[0].markdown("**Mois**")
    cols_h[1].markdown("**CA (FCFA)**")
    cols_h[2].markdown("**Objectif (FCFA)**")
    for i in range(n):
        c1, c2, c3 = st.columns(3)
        with c1: m = st.text_input("", months[i % 12], label_visibility="collapsed", key=f"s_m_{i}")
        with c2: ca = st.number_input("", 0.0, key=f"s_ca_{i}", value=float((i+1)*500000), label_visibility="collapsed")
        with c3: obj = st.number_input("", 0.0, key=f"s_obj_{i}", value=float((i+1)*600000), label_visibility="collapsed")
        data.append({"Mois": m, "CA": ca, "Objectif": obj, "Atteinte (%)": round(ca/obj*100, 1) if obj else 0})
    if st.button("📊 Générer le rapport", use_container_width=True, key="gen_sales"):
        from app.utils.doc_generator import generate_excel_report
        xlsx = generate_excel_report(pd.DataFrame(data), "Rapport de Ventes", lang=lang)
        save_report(user_id, "Rapport ventes", "xlsx", "ventes.xlsx", template_type="sales")
        st.download_button("⬇️ Télécharger", xlsx, "rapport_ventes.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="dl_sales", use_container_width=True)


def _budget(T, user_id, lang):
    n = st.number_input("Nombre de postes", 1, 20, 5, key="budget_n")
    data = []
    cols_h = st.columns(3)
    cols_h[0].markdown("**Poste**")
    cols_h[1].markdown("**Prévu (FCFA)**")
    cols_h[2].markdown("**Réalisé (FCFA)**")
    for i in range(int(n)):
        c1, c2, c3 = st.columns(3)
        with c1: cat = st.text_input("", f"Poste {i+1}", label_visibility="collapsed", key=f"b_c_{i}")
        with c2: prev = st.number_input("", 0.0, key=f"b_p_{i}", value=float((i+1)*100000), label_visibility="collapsed")
        with c3: real = st.number_input("", 0.0, key=f"b_r_{i}", value=float((i+1)*90000), label_visibility="collapsed")
        data.append({"Poste": cat, "Prévu": prev, "Réalisé": real, "Écart": real - prev})
    if st.button("💰 Générer le budget", use_container_width=True, key="gen_budget"):
        from app.utils.doc_generator import generate_excel_report
        xlsx = generate_excel_report(pd.DataFrame(data), "Budget Prévisionnel", lang=lang)
        save_report(user_id, "Budget", "xlsx", "budget.xlsx", template_type="budget")
        st.download_button("⬇️ Télécharger", xlsx, "budget.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="dl_budget", use_container_width=True)


def _inventory(T, user_id, lang):
    n = st.number_input("Nombre d'articles", 1, 50, 5, key="inv_n")
    data = []
    cols_h = st.columns(4)
    cols_h[0].markdown("**Référence**")
    cols_h[1].markdown("**Désignation**")
    cols_h[2].markdown("**Stock**")
    cols_h[3].markdown("**Prix (FCFA)**")
    for i in range(int(n)):
        c1, c2, c3, c4 = st.columns(4)
        with c1: ref = st.text_input("", f"REF-{i+1:03d}", label_visibility="collapsed", key=f"i_r_{i}")
        with c2: name = st.text_input("", f"Article {i+1}", label_visibility="collapsed", key=f"i_n_{i}")
        with c3: qty = st.number_input("", 0, key=f"i_q_{i}", value=100, label_visibility="collapsed")
        with c4: price = st.number_input("", 0.0, key=f"i_p_{i}", value=5000.0, label_visibility="collapsed")
        data.append({"Référence": ref, "Désignation": name, "Stock": qty, "Prix": price, "Valeur": qty * price})
    if st.button("📦 Générer l'inventaire", use_container_width=True, key="gen_inventory"):
        from app.utils.doc_generator import generate_excel_report
        xlsx = generate_excel_report(pd.DataFrame(data), "Inventaire", lang=lang)
        save_report(user_id, "Inventaire", "xlsx", "inventaire.xlsx", template_type="inventory")
        st.download_button("⬇️ Télécharger", xlsx, "inventaire.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="dl_inv", use_container_width=True)


def _marketing(T, user_id, lang):
    df = pd.DataFrame({
        "KPI": ["Visites", "Leads", "Conversions", "CA généré", "Coût/Lead", "ROI (%)"],
        "Valeur": [15000, 450, 85, 4250000, 2250, 312],
        "Objectif": [12000, 400, 80, 4000000, 2500, 300],
    })
    df_ed = st.data_editor(df, use_container_width=True, key="mkt_editor")
    if st.button("📣 Générer le rapport", use_container_width=True, key="gen_mkt"):
        from app.utils.doc_generator import generate_excel_report
        xlsx = generate_excel_report(df_ed, "Rapport Marketing", lang=lang)
        save_report(user_id, "Marketing", "xlsx", "marketing.xlsx", template_type="marketing")
        st.download_button("⬇️ Télécharger", xlsx, "rapport_marketing.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="dl_mkt", use_container_width=True)


def _hr(T, user_id, lang):
    df = pd.DataFrame({
        "Département": ["Commercial", "Technique", "RH", "Finance", "Marketing"],
        "Effectif": [25, 40, 8, 12, 15],
        "Absences (j)": [12, 8, 3, 5, 7],
        "Recrutements": [3, 5, 1, 0, 2],
        "Satisfaction (%)": [78, 85, 91, 82, 88],
    })
    df_ed = st.data_editor(df, use_container_width=True, key="hr_editor")
    if st.button("👥 Générer le rapport RH", use_container_width=True, key="gen_hr"):
        from app.utils.doc_generator import generate_excel_report
        xlsx = generate_excel_report(df_ed, "Rapport RH", lang=lang)
        save_report(user_id, "RH", "xlsx", "rh.xlsx", template_type="hr")
        st.download_button("⬇️ Télécharger", xlsx, "rapport_rh.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="dl_hr", use_container_width=True)


def _get_empty(tmpl_id):
    cols_map = {
        "invoice": ["Description", "Quantité", "Prix HT (FCFA)", "Total HT (FCFA)"],
        "sales": ["Mois", "CA (FCFA)", "Objectif (FCFA)", "Atteinte (%)"],
        "budget": ["Poste", "Prévu (FCFA)", "Réalisé (FCFA)", "Écart (FCFA)"],
        "inventory": ["Référence", "Désignation", "Stock", "Prix unitaire (FCFA)", "Valeur stock (FCFA)"],
        "marketing": ["KPI", "Valeur", "Objectif", "Écart"],
        "hr": ["Département", "Effectif", "Absences (j)", "Recrutements", "Satisfaction (%)"],
    }
    df = pd.DataFrame(columns=cols_map.get(tmpl_id, []))
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Template")
    output.seek(0)
    return output.read()
