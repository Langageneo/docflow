"""
Utilitaires de traitement des données
"""

import pandas as pd
import numpy as np
import os
import io
import hashlib
from datetime import datetime
from app.config import Config


def load_dataframe(file_path: str) -> pd.DataFrame:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                return pd.read_csv(file_path, encoding=enc)
            except UnicodeDecodeError:
                continue
        return pd.read_csv(file_path, encoding="utf-8", errors="replace")
    elif ext in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Format non supporté: {ext}")


def save_uploaded_file(uploaded_file) -> tuple:
    os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    stored_name = f"{timestamp}_{hashlib.md5(uploaded_file.name.encode()).hexdigest()[:8]}{ext}"
    file_path = os.path.join(Config.UPLOAD_DIR, stored_name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return stored_name, file_path


def compute_statistics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "shape": {"rows": 0, "cols": len(df.columns)},
            "missing": 0, "missing_by_col": {}, "duplicates": 0,
            "dtypes": {}, "memory_mb": 0,
        }
    stats = {
        "shape": {"rows": len(df), "cols": len(df.columns)},
        "missing": int(df.isnull().sum().sum()),
        "missing_by_col": df.isnull().sum().to_dict(),
        "duplicates": int(df.duplicated().sum()),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
    }
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        desc = df[numeric_cols].describe().round(2)
        stats["numeric_summary"] = desc.to_dict()
        stats["numeric_cols"] = numeric_cols
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if cat_cols:
        stats["categorical_cols"] = cat_cols
        stats["value_counts"] = {}
        for col in cat_cols[:5]:
            vc = df[col].value_counts().head(10)
            stats["value_counts"][col] = vc.to_dict()
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr().round(3)
        stats["correlation"] = corr.to_dict()
    return stats


def generate_insights(df: pd.DataFrame, lang: str = "fr") -> list:
    insights = []
    if df.empty or len(df) == 0:
        if lang == "fr":
            insights.append("⚠️ Le fichier est vide — aucune donnée à analyser.")
        else:
            insights.append("⚠️ The file is empty — no data to analyze.")
        return insights

    n_rows, n_cols = df.shape
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object"]).columns.tolist()

    if lang == "fr":
        insights.append(f"📊 Le jeu de données contient **{n_rows:,} lignes** et **{n_cols} colonnes**.")
        missing = df.isnull().sum().sum()
        missing_pct = (missing / (n_rows * n_cols) * 100) if n_rows * n_cols > 0 else 0
        if missing == 0:
            insights.append("✅ Aucune valeur manquante détectée — les données sont complètes.")
        elif missing_pct < 5:
            insights.append(f"⚠️ **{missing}** valeurs manquantes ({missing_pct:.1f}%) — impact faible.")
        else:
            worst_col = df.isnull().sum().idxmax()
            insights.append(f"🔴 **{missing}** valeurs manquantes ({missing_pct:.1f}%). La colonne **{worst_col}** est la plus affectée.")
        dupes = df.duplicated().sum()
        if dupes > 0:
            insights.append(f"⚠️ **{dupes}** lignes dupliquées détectées ({dupes/n_rows*100:.1f}% des données).")
        else:
            insights.append("✅ Aucun doublon trouvé dans les données.")
        for col in numeric_cols[:3]:
            col_data = df[col].dropna()
            if len(col_data) == 0:
                continue
            mean_val = col_data.mean()
            std_val = col_data.std()
            cv = (std_val / mean_val * 100) if mean_val != 0 else 0
            if cv > 50:
                insights.append(f"📈 La colonne **{col}** montre une forte variabilité (CV={cv:.0f}%).")
            else:
                insights.append(f"📉 La colonne **{col}** est stable (moyenne={mean_val:.2f}, écart-type={std_val:.2f}).")
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr().abs()
            corr_values = corr_matrix.values.copy()
            np.fill_diagonal(corr_values, 0)
            if corr_values.max() > 0.8:
                idx = corr_matrix.stack().idxmax()
                insights.append(f"🔗 Forte corrélation détectée entre **{idx[0]}** et **{idx[1]}**.")
        for col in cat_cols[:2]:
            n_unique = df[col].nunique()
            if n_rows > 0 and n_unique > 1 and n_unique / n_rows <= 0.9:
                top_val = df[col].value_counts().index[0]
                top_pct = df[col].value_counts().iloc[0] / n_rows * 100
                insights.append(f"🏷️ Dans **{col}**, la valeur dominante est **{top_val}** ({top_pct:.1f}%).")
    else:
        insights.append(f"📊 Dataset contains **{n_rows:,} rows** and **{n_cols} columns**.")
        missing = df.isnull().sum().sum()
        missing_pct = (missing / (n_rows * n_cols) * 100) if n_rows * n_cols > 0 else 0
        if missing == 0:
            insights.append("✅ No missing values detected — data is complete.")
        elif missing_pct < 5:
            insights.append(f"⚠️ **{missing}** missing values ({missing_pct:.1f}%) — low impact.")
        else:
            worst_col = df.isnull().sum().idxmax()
            insights.append(f"🔴 **{missing}** missing values ({missing_pct:.1f}%). Column **{worst_col}** is most affected.")
        dupes = df.duplicated().sum()
        if dupes > 0:
            insights.append(f"⚠️ **{dupes}** duplicate rows detected ({dupes/n_rows*100:.1f}% of data).")
        else:
            insights.append("✅ No duplicates found in the dataset.")
        for col in numeric_cols[:3]:
            col_data = df[col].dropna()
            if len(col_data) == 0:
                continue
            mean_val = col_data.mean()
            std_val = col_data.std()
            cv = (std_val / mean_val * 100) if mean_val != 0 else 0
            if cv > 50:
                insights.append(f"📈 Column **{col}** shows high variability (CV={cv:.0f}%).")
            else:
                insights.append(f"📉 Column **{col}** is stable (mean={mean_val:.2f}, std={std_val:.2f}).")
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr().abs()
            corr_values = corr_matrix.values.copy()
            np.fill_diagonal(corr_values, 0)
            if corr_values.max() > 0.8:
                idx = corr_matrix.stack().idxmax()
                insights.append(f"🔗 Strong correlation detected between **{idx[0]}** and **{idx[1]}**.")
        for col in cat_cols[:2]:
            n_unique = df[col].nunique()
            if n_rows > 0 and n_unique > 1 and n_unique / n_rows <= 0.9:
                top_val = df[col].value_counts().index[0]
                top_pct = df[col].value_counts().iloc[0] / n_rows * 100
                insights.append(f"🏷️ In **{col}**, dominant value is **{top_val}** ({top_pct:.1f}%).")
    return insights


def clean_dataframe(df: pd.DataFrame, options: dict) -> tuple:
    original_shape = df.shape
    report = {}
    df_clean = df.copy()

    if options.get("remove_duplicates"):
        before = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        report["duplicates_removed"] = before - len(df_clean)

    if options.get("fill_missing"):
        method = options.get("fill_method", "mean")
        filled = 0
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        cat_cols = df_clean.select_dtypes(include=["object"]).columns
        if method == "mean":
            for col in numeric_cols:
                missing = df_clean[col].isnull().sum()
                df_clean[col] = df_clean[col].fillna(df_clean[col].mean())
                filled += missing
        elif method == "median":
            for col in numeric_cols:
                missing = df_clean[col].isnull().sum()
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
                filled += missing
        elif method == "zero":
            for col in numeric_cols:
                missing = df_clean[col].isnull().sum()
                df_clean[col] = df_clean[col].fillna(0)
                filled += missing
        elif method == "drop":
            before = len(df_clean)
            df_clean = df_clean.dropna()
            filled = (before - len(df_clean)) * df_clean.shape[1]
        for col in cat_cols:
            missing = df_clean[col].isnull().sum()
            df_clean[col] = df_clean[col].fillna("N/A")
            filled += missing
        report["missing_filled"] = filled

    if options.get("normalize_columns"):
        old_cols = df_clean.columns.tolist()
        df_clean.columns = (
            df_clean.columns
            .str.strip()
            .str.lower()
            .str.replace(r"[^a-zA-Z0-9_]", "_", regex=True)
            .str.replace(r"_+", "_", regex=True)
            .str.strip("_")
        )
        report["columns_normalized"] = len([a for a, b in zip(old_cols, df_clean.columns) if a != b])

    if options.get("fix_formats"):
        fixed = 0
        for col in df_clean.select_dtypes(include=["object"]).columns:
            try:
                converted = pd.to_numeric(df_clean[col].str.replace(",", ".").str.strip(), errors="coerce")
                if converted.notna().sum() / len(df_clean) > 0.8:
                    df_clean[col] = converted
                    fixed += 1
            except Exception:
                pass
        report["formats_fixed"] = fixed

    report["original_shape"] = original_shape
    report["final_shape"] = df_clean.shape
    report["rows_removed"] = original_shape[0] - df_clean.shape[0]
    return df_clean, report


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} Ko"
    else:
        return f"{size_bytes/1024/1024:.1f} Mo"
