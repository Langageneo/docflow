"""
Utilitaires Google Sheets API
"""

import os
import pandas as pd
from datetime import datetime

CREDENTIALS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "credentials.json")


def is_configured() -> bool:
    return os.path.exists(CREDENTIALS_PATH)


def get_client():
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scopes)
    return gspread.authorize(creds)


def export_dataframe_to_sheets(df, title, share_email=None, include_stats=True, lang="fr"):
    client = get_client()
    spreadsheet = client.create(title)

    ws_data = spreadsheet.sheet1
    ws_data.update_title("Données" if lang == "fr" else "Data")

    headers = df.columns.tolist()
    ws_data.append_row(headers)

    rows = df.fillna("").astype(str).values.tolist()
    if rows:
        ws_data.append_rows(rows)

    header_format = {
        "backgroundColor": {"red": 0.914, "green": 0.271, "blue": 0.376},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
        "horizontalAlignment": "CENTER",
    }
    ws_data.format(f"A1:{_col_letter(len(headers))}1", header_format)

    for i in range(2, len(rows) + 2):
        bg = {"red": 0.118, "green": 0.118, "blue": 0.188} if i % 2 == 0 else {"red": 0.086, "green": 0.129, "blue": 0.243}
        ws_data.format(f"A{i}:{_col_letter(len(headers))}{i}", {
            "backgroundColor": bg,
            "textFormat": {"foregroundColor": {"red": 0.918, "green": 0.918, "blue": 0.918}},
        })

    spreadsheet.batch_update({"requests": [{"updateSheetProperties": {
        "properties": {"sheetId": ws_data.id, "gridProperties": {"frozenRowCount": 1}},
        "fields": "gridProperties.frozenRowCount"
    }}]})

    if include_stats:
        import numpy as np
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            title_stats = "Statistiques" if lang == "fr" else "Statistics"
            ws_stats = spreadsheet.add_worksheet(title=title_stats, rows=20, cols=len(numeric_df.columns) + 2)
            desc = numeric_df.describe().reset_index()
            ws_stats.append_row(desc.columns.tolist())
            for _, row in desc.iterrows():
                ws_stats.append_row([round(v, 3) if isinstance(v, float) else v for v in row.tolist()])
            ws_stats.format(f"A1:{_col_letter(len(desc.columns))}1", header_format)

    summary_title = "Résumé" if lang == "fr" else "Summary"
    ws_summary = spreadsheet.add_worksheet(title=summary_title, rows=20, cols=4)
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    summary_rows = [
        ["DocFlow — Rapport généré le" if lang == "fr" else "DocFlow — Report generated on", date_str],
        [""],
        ["Indicateur" if lang == "fr" else "Metric", "Valeur" if lang == "fr" else "Value"],
        ["Lignes totales" if lang == "fr" else "Total Rows", len(df)],
        ["Colonnes" if lang == "fr" else "Columns", len(df.columns)],
        ["Valeurs manquantes" if lang == "fr" else "Missing Values", int(df.isnull().sum().sum())],
        ["Doublons" if lang == "fr" else "Duplicates", int(df.duplicated().sum())],
    ]
    for row in summary_rows:
        ws_summary.append_row(row)

    ws_summary.format("A1:B1", {
        "textFormat": {"bold": True, "fontSize": 14,
                       "foregroundColor": {"red": 0.914, "green": 0.271, "blue": 0.376}},
    })
    ws_summary.format("A3:B3", header_format)

    spreadsheet.share(None, perm_type="anyone", role="reader")
    if share_email and share_email.strip():
        spreadsheet.share(share_email.strip(), perm_type="user", role="writer")

    return {"url": spreadsheet.url, "id": spreadsheet.id, "title": title, "sheets": spreadsheet.worksheets()}


def export_csv_to_sheets(csv_content, title, share_email=None, lang="fr"):
    import io
    df = pd.read_csv(io.BytesIO(csv_content))
    return export_dataframe_to_sheets(df, title, share_email=share_email, lang=lang)


def export_excel_to_sheets(excel_content, title, share_email=None, lang="fr"):
    import io
    df = pd.read_excel(io.BytesIO(excel_content))
    return export_dataframe_to_sheets(df, title, share_email=share_email, lang=lang)


def _col_letter(n):
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result
