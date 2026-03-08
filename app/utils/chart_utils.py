"""
Génération de graphiques avec Plotly
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from app.config import Config

DARK_TEMPLATE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.03)",
    font=dict(color="#eaeaea", family="DM Sans"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.1)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.1)"),
    legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="rgba(255,255,255,0.1)", borderwidth=1),
)

COLORS = Config.CHART_COLORS


def apply_dark_theme(fig):
    fig.update_layout(**DARK_TEMPLATE)
    return fig


def create_bar_chart(df, x_col, y_col, title=""):
    fig = px.bar(df, x=x_col, y=y_col, title=title, color_discrete_sequence=COLORS)
    fig.update_traces(marker_line_width=0)
    return apply_dark_theme(fig)


def create_line_chart(df, x_col, y_col, title=""):
    fig = px.line(df, x=x_col, y=y_col, title=title, color_discrete_sequence=COLORS)
    fig.update_traces(line_width=2.5)
    return apply_dark_theme(fig)


def create_scatter_chart(df, x_col, y_col, title=""):
    fig = px.scatter(df, x=x_col, y=y_col, title=title, color_discrete_sequence=COLORS)
    fig.update_traces(marker=dict(size=8, opacity=0.7))
    return apply_dark_theme(fig)


def create_pie_chart(df, names_col, values_col=None, title=""):
    if values_col:
        fig = px.pie(df, names=names_col, values=values_col, title=title, color_discrete_sequence=COLORS)
    else:
        counts = df[names_col].value_counts().reset_index()
        counts.columns = [names_col, "count"]
        fig = px.pie(counts, names=names_col, values="count", title=title, color_discrete_sequence=COLORS)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return apply_dark_theme(fig)


def create_histogram(df, col, title=""):
    fig = px.histogram(df, x=col, title=title, color_discrete_sequence=COLORS, nbins=30)
    fig.update_traces(marker_line_width=0.5, marker_line_color="rgba(255,255,255,0.2)")
    return apply_dark_theme(fig)


def create_box_plot(df, y_col, x_col=None, title=""):
    if x_col:
        fig = px.box(df, x=x_col, y=y_col, title=title, color_discrete_sequence=COLORS)
    else:
        fig = px.box(df, y=y_col, title=title, color_discrete_sequence=COLORS)
    return apply_dark_theme(fig)


def create_correlation_heatmap(df, title="Matrice de corrélation"):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        return None
    corr = df[numeric_cols].corr().round(2)
    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale=[[0, "#3498db"], [0.5, "#1a1a2e"], [1, "#e94560"]],
        zmin=-1, zmax=1,
        text=corr.values.round(2),
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False
    ))
    fig.update_layout(title=title)
    return apply_dark_theme(fig)


def create_missing_values_chart(df, lang="fr"):
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=True)
    if missing.empty:
        return None
    label = "Valeurs manquantes" if lang == "fr" else "Missing Values"
    fig = go.Figure(go.Bar(
        x=missing.values, y=missing.index, orientation="h",
        marker=dict(color="#e94560", opacity=0.85),
        text=missing.values, textposition="outside"
    ))
    fig.update_layout(title=label, xaxis_title=label, yaxis_title="")
    return apply_dark_theme(fig)


def auto_chart(df, lang="fr"):
    if df.empty:
        return []
    charts = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    missing_chart = create_missing_values_chart(df, lang)
    if missing_chart:
        charts.append(("missing", missing_chart))

    for col in numeric_cols[:3]:
        title = f"Distribution — {col}"
        charts.append((f"hist_{col}", create_histogram(df, col, title)))

    if cat_cols and numeric_cols:
        cat = cat_cols[0]
        num = numeric_cols[0]
        if df[cat].nunique() <= 20:
            agg = df.groupby(cat)[num].mean().reset_index().sort_values(num, ascending=False).head(15)
            title = f"{num} par {cat}" if lang == "fr" else f"{num} by {cat}"
            charts.append((f"bar_{cat}_{num}", create_bar_chart(agg, cat, num, title)))

    if len(numeric_cols) >= 2:
        title = "Matrice de corrélation" if lang == "fr" else "Correlation Matrix"
        hm = create_correlation_heatmap(df, title)
        if hm:
            charts.append(("correlation", hm))

    if cat_cols:
        for col in cat_cols:
            if 2 <= df[col].nunique() <= 8:
                title = f"Répartition — {col}" if lang == "fr" else f"Distribution — {col}"
                charts.append((f"pie_{col}", create_pie_chart(df, col, title=title)))
                break

    return charts
