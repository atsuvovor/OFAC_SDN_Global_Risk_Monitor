###########################
# risk_report_generator.py
# Author: Atsu Vovor
# Date: 2025-11-09
###########################
from __future__ import annotations
from typing import Optional, Tuple
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import html
import re
from html import unescape
from fpdf import FPDF
import os
from config import (
    APP_NAME,
    STREAMLIT_LAYOUT,
    STREAMLIT_PAGE_ICON,
    DATA_DIR,
    REPORTS_DIR,
    CACHE_DIR,
    SDN_PATH,
    ADD_PATH,
    MAP_PATH,
    RISK_COLOR_MAP,
    RISK_SCORE_MAP,
    LLM_MODEL_PATH,
    USE_RAG,
    IS_DOCKER,
    IS_STREAMLIT_CLOUD,
    ARCHITECTURE_PATH
)

ABOUT_MARKDOWN_INTRO = """
# 📊 OFAC SDN Global Risk Monitor: Compliance Analytics Dashboard

The **OFAC SDN Global Risk Monitor** is an interactive data visualization project designed to empower compliance and financial risk teams with rapid, quantifiable assessment of sanctions exposure.  
This solution analyzes *Specially Designated Nationals (SDNs)* data to highlight geographic concentration and entity type exposure across key jurisdictions.
It leverages Python’s data stack and Streamlit’s interactive capabilities for efficient
reporting and compliance monitoring.

---
"""
ABOUT_MARKDOWN_DETAILS = """

## 🔬 Analytical Core: Risk Calculation & Logic

A tiered methodology assigns **Risk Ratings** based on total distinct entities per country.

| Total Distinct Entities (SDNs) | Risk Rating | Color Logic |
| :--- | :--- | :--- |
| **> 1000** | **Critical** | 🔴 Red |
| **> 800 to ≤ 1000** | **High** | 🔴 Red |
| **> 600 to ≤ 800** | **Medium High** | 🟠 Orange |
| **> 400 to ≤ 600** | **Medium** | 🟡 Yellow |
| **> 200 to ≤ 400** | **Medium Low** | 🟤 Light Yellow |
| **≤ 200** | **Low** | 🟢 Green |


---

## 🔝 Key Performance & Risk Indicators (KPI/KRI)

| Indicator | Type | Definition and Business Insight |
| :--- | :--- | :--- |
| **Total Distinct Entities** | **KPI** | Count of unique sanctioned entities across jurisdictions — measures total sanctions volume. |
| **Critical Risk Jurisdictions** | **KRI** | Number of countries flagged as *Critical* — indicates top compliance priorities. |
| **Non-Individual Entity Ratio** | **KRI** | Percentage of organizations or vessels (non-individuals) among SDNs — highlights systemic exposure. |
| **Top SDN Concentration** | **KPI** | The highest total count of entities per country (e.g., 1,018), defining concentration risk ceiling. |

---

## 📂 Data Sources

| File Name | Description |
| :--- | :--- |
| **sdn.csv** | Core SDN entity data including names, SDN Type (Individual/Non-Individual), and sanction program details. |
| **add.csv** | Supplementary address data linked by `ent_num`, providing country-level geographic context. |

---

## 🛠️ Technology Stack

The **Python + Streamlit** implementation of the OFAC Risk Dashboard modernizes the original Excel-based model into a fully automated, interactive web application.
It integrates data cleansing, dynamic risk modeling, and executive reporting — providing a scalable and intelligent platform for sanctions risk monitoring and analytics.

| Component                         | Technology Used                                  | Function                                                                                                                                                                                                                                                     |
| :-------------------------------- | :----------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Data Integration & ETL**        | **Pandas**                                       | Reads, cleans, and merges the `sdn.csv`, `add.csv`, and `map.csv` datasets on the common key (`ent_num`). Handles invalid or missing country values, applies normalization, and maintains referential integrity between entity and address records.          |
| **Risk Modeling & Calculation**   | **Custom Python Logic (Risk Scoring Functions)** | Implements rule-based risk scoring through defined thresholds using `apply_risk_rating()`. Generates `Risk_Level` and `Risk_Score` columns based on SDN entity volumes per country and sanction program.                                                     |
| **Visualization & Interactivity** | **Plotly Express + Streamlit UI Components**     | Provides dynamic, interactive charts (heatmaps, bar charts, and distributions) with filters for program and country selection, toggle between aggregation types, and detailed tooltips. Uses Streamlit for responsive layout and real-time user interaction. |
| **Automated Reporting**           | **FPDF + HTML Export**                           | Generates downloadable executive-style reports in both PDF and HTML formats, embedding visualizations, legends, and dynamically generated data stories summarizing key business insights.                                                                    |
| **AI-Driven Insights (Optional)** | **GPT-based Narrative Generator**                | Produces an adaptive “Data Story” section summarizing risk concentration, top jurisdictions, and actionable compliance insights based on filtered data selections.    

---|
## 🌐 Deployment

The project is hosted publicly on **GitHub** and deployed on **Streamlit Cloud** for global access.

- **[GitHub Repository](https://github.com/atsuvovor/OFAC_SDN_Global_Risk_Monitor/tree/main)**
- **Streamlit Dashboard:** [Your Streamlit Cloud App URL]

---
"""
ABOUT_MARKDOWN_FOOT ="""
---
*© 2025 Atsu Vovor — Consultant, Data & Analytics | OFAC SDN Risk Monitor Project 
Ph: 416-795-8246 | ✉️ atsu.vovor@bell.net  
🔗 [LinkedIn ](https://www.linkedin.com/in/atsu-vovor-mmai-9188326/)|   [GitHub](https://atsuvovor.github.io/projects_portfolio.github.io/) |   [Tableau Portfolio](https://public.tableau.com/app/profile/atsu.vovor8645/vizzes)  
📍 Mississauga ON   

### Thank you for visiting!🙏
# ---------------------------
# Small helpers
# ---------------------------
def _ensure_numeric(df: pd.DataFrame, col: str, default: float = 0.0) -> pd.Series:
    return pd.to_numeric(df.get(col, pd.Series(dtype=float)), errors="coerce").fillna(default)

def _annotate_heatmap(fig: go.Figure, z: np.ndarray, x: list, y: list, font_size: int = 12):
    """
    Add text annotations to a heatmap figure (z matrix) centered in each cell.
    """
    annotations = []
    for i, yi in enumerate(y):
        for j, xj in enumerate(x):
            val = z[i][j]
            # skip annotation for zero/NaN if you prefer, but show zeros too for clarity
            txt = str(round(float(val), 2)) if (pd.notna(val)) else ""
            annotations.append(
                dict(
                    x=xj,
                    y=yi,
                    text=txt,
                    showarrow=False,
                    font=dict(color="white", size=font_size),
                    xanchor="center",
                    yanchor="middle",
                )
            )
    fig.update_layout(annotations=annotations)

# ---------------------------
# Core chart functions
# ---------------------------

def generate_donut_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.pie(
        df,
        names="Country",
        values="Total Distinct Entities",
        hole=0.55,
        title="Total Distinct Entities by Country",
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(t=50, b=0, l=0, r=0), height=520)
    return fig

def generate_stacked_bar(df: pd.DataFrame) -> go.Figure:
    df = df.sort_values("Total Distinct Entities", ascending=False)
    fig = go.Figure(
        [
            go.Bar(name="Distinct Non-Individuals", x=df["Country"], y=df["Distinct Non-Individuals"], marker_color="gray"),
            go.Bar(name="Distinct Individuals", x=df["Country"], y=df["Distinct Individuals"], marker_color="orange"),
            go.Bar(name="Total Distinct Entities", x=df["Country"], y=df["Total Distinct Entities"], marker_color="blue"),
        ]
    )
    fig.update_layout(barmode="stack", xaxis_tickangle=-45, height=600, margin=dict(t=50))
    return fig

def generate_percent_stacked(df: pd.DataFrame) -> go.Figure:
    df = df.copy()
    total = df[["Distinct Non-Individuals", "Distinct Individuals", "Total Distinct Entities"]].sum(axis=1)
    for col in ["Distinct Non-Individuals", "Distinct Individuals", "Total Distinct Entities"]:
        df[f"{col} %"] = (df[col] / total * 100).fillna(0)
    fig = go.Figure(
        [
            go.Bar(name="Total Entities %", x=df["Country"], y=df["Total Distinct Entities %"], marker_color="blue"),
            go.Bar(name="Individuals %", x=df["Country"], y=df["Distinct Individuals %"], marker_color="orange"),
            go.Bar(name="Non-Individuals %", x=df["Country"], y=df["Distinct Non-Individuals %"], marker_color="gray"),
        ]
    )
    # legend placed under the chart
    fig.update_layout(
        barmode="stack",
        xaxis_tickangle=-45,
        height=600,
        legend=dict(orientation="h", y=-0.25, x=0.0),
        margin=dict(t=50, b=80),
    )
    return fig

def generate_risk_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Heatmap with:
    - white cell borders (xgap/ygap)
    - annotated risk scores in each cell
    - pivot_table aggfunc='mean' to be resilient to duplicates
    """
    # Long form and mapping to numeric scores
    df_long = df.melt(
        id_vars=["Country"],
        value_vars=["Rating - Personal & Non-Personal", "Rating - Personal", "Rating - Non-Personal"],
        var_name="Risk Type",
        value_name="Risk Level",
    )
    df_long["Risk Score"] = df_long["Risk Level"].map(RISK_SCORE_MAP).fillna(0)

    pivot = df_long.pivot_table(index="Country", columns="Risk Type", values="Risk Score", aggfunc="mean", fill_value=0)
    # ensure ordering of columns (if any missing)
    x_labels = pivot.columns.tolist()
    y_labels = pivot.index.tolist()
    z = pivot.values.astype(float)

    # heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=x_labels,
            y=y_labels,
            colorscale=[
                [0.0, RISK_COLOR_MAP["Low"]],
                [0.2, RISK_COLOR_MAP["Medium Low"]],
                [0.4, RISK_COLOR_MAP["Medium"]],
                [0.6, RISK_COLOR_MAP["Medium High"]],
                [0.8, RISK_COLOR_MAP["High"]],
                [1.0, RISK_COLOR_MAP["Critical"]],
            ],
            zmin=1,
            zmax=6,
            showscale=True,
            colorbar=dict(title="Risk Level (Score)", tickvals=[1,2,3,4,5,6], ticktext=["Low","Med Low","Med","Med High","High","Critical"]),
            xgap=2,  # white border width between cells
            ygap=2,
            hovertemplate="<b>%{y}</b><br>Risk Type: %{x}<br>Avg Risk Score: %{z}<extra></extra>",
        )
    )

    # add annotations (risk scores) centered in each cell
    _annotate_heatmap(fig, z, x_labels, y_labels, font_size=11)

    fig.update_layout(
        title="Country Risk Heatmap",
        xaxis_title="Risk Type",
        yaxis_title="Country",
        height=600,
        margin=dict(t=70, b=50, l=120, r=40),
    )
    # put white grid behind using paper_bgcolor? xgap/ygap already gives white borders
    return fig

# ---------------------------
# Program-level visuals (used by pivot/risk module)
# ---------------------------

def generate_program_bar_chart(pivot_df: pd.DataFrame) -> go.Figure:
    # choose an aggregation column (SDN_Count or Total_SDNs)
    y_col = "Avg_Risk_Score" if "Avg_Risk_Score" in pivot_df.columns else ("SDN_Count" if "SDN_Count" in pivot_df.columns else pivot_df.columns[-1])
    fig = px.bar(pivot_df, x="Country", y=y_col, color="Sanctions Program", title="SDN Concentration by Sanctions Program and Country")
    fig.update_layout(xaxis_tickangle=-45, yaxis_title=y_col, height=600, margin=dict(t=70))
    return fig

def generate_program_heatmap(pivot_df: pd.DataFrame) -> go.Figure:
    """
    Program heatmap using pivot_table(..., aggfunc='mean'), white borders, and cell annotations.
    """
    val_col = "Avg_Risk_Score" if "Avg_Risk_Score" in pivot_df.columns else ("SDN_Count" if "SDN_Count" in pivot_df.columns else None)
    if val_col is None:
        raise ValueError("pivot_df must contain 'Avg_Risk_Score' or 'SDN_Count'")

    pivot_heat = pivot_df.pivot_table(index="Country", columns="Sanctions Program", values=val_col, aggfunc="mean", fill_value=0)
    x_labels = pivot_heat.columns.tolist()
    y_labels = pivot_heat.index.tolist()
    z = pivot_heat.values.astype(float)

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=x_labels,
            y=y_labels,
            colorscale=[
                [0.0, RISK_COLOR_MAP["Low"]],
                [0.2, RISK_COLOR_MAP["Medium Low"]],
                [0.4, RISK_COLOR_MAP["Medium"]],
                [0.6, RISK_COLOR_MAP["Medium High"]],
                [0.8, RISK_COLOR_MAP["High"]],
                [1.0, RISK_COLOR_MAP["Critical"]],
            ],
            zmin=z.min() if z.size else 0,
            zmax=z.max() if z.size else 1,
            colorbar=dict(title=f"{val_col} (aggregated)"),
            xgap=2,
            ygap=2,
            hovertemplate="<b>%{y}</b><br>Program: %{x}<br>Value: %{z}<extra></extra>",
        )
    )

    _annotate_heatmap(fig, z, x_labels, y_labels, font_size=11)

    fig.update_layout(
        title="Cross-Border Sanctions Program Risk Concentration",
        xaxis_title="Sanctions Program",
        yaxis_title="Country",
        height=520,
        margin=dict(t=80, l=120, r=40, b=80),
    )
    return fig

# ---------------------------
# Data story generator
# ---------------------------
def remove_non_ascii(text: str) -> str:
    """Remove or replace non-ASCII characters safely for PDF export."""
    return text.encode("ascii", "ignore").decode("ascii")

def create_pdf_from_html(story_html: str, pdf_path: str):
    """
    Convert an HTML text block into a well-formatted PDF file.
    Handles Unicode and fallback fonts for Streamlit Cloud.
    """
    pdf = FPDF()
    pdf.add_page()

    # --- Font setup ---
    font_dir = os.path.join(os.path.dirname(__file__), "fonts")
    font_path = os.path.join(font_dir, "DejaVuSans.ttf")

    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", "", 12)
    else:
        pdf.set_font("Helvetica", "", 12)

    # --- Clean HTML and write ---
    plain = re.sub(r"<[^>]+>", "", story_html)  # remove HTML tags
    plain = unescape(plain)
    plain = remove_non_ascii(plain)

    for line in plain.split("\n"):
        try:
            pdf.multi_cell(0, 7, line)
        except Exception:
            pdf.multi_cell(0, 7, remove_non_ascii(line))

    pdf.output(pdf_path)
    return pdf_path
    
def generate_data_story(df_filtered: pd.DataFrame) -> str:
    """
    Build an executive-style, dynamic data story from filtered metrics/master data.
    Produces: top 5 countries, dominant risk drivers, entity mix, recommended actions.
    Returns markdown-formatted string (safe to insert in HTML).
    """
    if df_filtered is None or df_filtered.empty:
        return "<p><em>No data available to generate a data story.</em></p>"

    # Work on a copy
    df = df_filtered.copy()

    # Ensure counts numeric
    df["Total Distinct Entities"] = pd.to_numeric(df.get("Total Distinct Entities", 0), errors="coerce").fillna(0).astype(int)
    df["Distinct Individuals"] = pd.to_numeric(df.get("Distinct Individuals", 0), errors="coerce").fillna(0).astype(int)
    df["Distinct Non-Individuals"] = pd.to_numeric(df.get("Distinct Non-Individuals", 0), errors="coerce").fillna(0).astype(int)

    # Top 5 countries
    top5 = df.nlargest(5, "Total Distinct Entities")[["Country", "Total Distinct Entities"]]
    top5_list = ", ".join(f"{r.Country} ({int(r['Total Distinct Entities'])})" for _, r in top5.iterrows())

    # Dominant risk rating
    if "Rating - Personal & Non-Personal" in df.columns:
        risk_counts = df["Rating - Personal & Non-Personal"].value_counts()
        dominant_risk = risk_counts.idxmax() if not risk_counts.empty else None
        dominant_count = int(risk_counts.max()) if not risk_counts.empty else 0
        dominant_share = (dominant_count / risk_counts.sum() * 100) if risk_counts.sum() > 0 else 0
    else:
        dominant_risk = None
        dominant_share = 0

    total_entities = df["Total Distinct Entities"].sum()
    individuals = df["Distinct Individuals"].sum()
    non_individuals = df["Distinct Non-Individuals"].sum()
    indiv_pct = (individuals / total_entities * 100) if total_entities > 0 else 0
    nonind_pct = (non_individuals / total_entities * 100) if total_entities > 0 else 0

    avg_risk_score = None
    # attempt to compute average risk score if present
    if "Rating - Personal & Non-Personal" in df.columns:
        # map rating -> score and compute weighted average
        df["__score__"] = df["Rating - Personal & Non-Personal"].map(RISK_SCORE_MAP).fillna(0)
        avg_risk_score = df["__score__"].mean()

    # build markdown story (escaped where needed)
    story_lines = []
    story_lines.append(f"<h3>Executive Data Story</h3>")
    story_lines.append(f"<p><strong>Top 5 countries by SDN exposure:</strong> {html.escape(top5_list)}</p>")
    story_lines.append(f"<p><strong>Total distinct entities in view:</strong> {int(total_entities):,}</p>")
    story_lines.append(f"<p><strong>Entity mix:</strong> Individuals {indiv_pct:.1f}% | Non-Individuals {nonind_pct:.1f}%.</p>")

    if dominant_risk:
        story_lines.append(f"<p><strong>Dominant risk tier:</strong> {html.escape(dominant_risk)} (~{dominant_share:.1f}% of rows)</p>")

    if avg_risk_score is not None:
        story_lines.append(f"<p><strong>Average risk score (approx.):</strong> {avg_risk_score:.2f}</p>")

    # recommendations
    story_lines.append("<h4>Key recommendations</h4>")
    story_lines.append("<ul>")
    story_lines.append("<li>Prioritize enhanced due diligence for top countries listed above (focus on both Individuals and Non-Individuals).</li>")
    story_lines.append("<li>Monitor program-specific spikes using the Program heatmap to find cross-border nexus points.</li>")
    story_lines.append("<li>Investigate high Average Risk Score cells and consider transaction/blocking rules for those jurisdictions.</li>")
    story_lines.append("</ul>")

    return "\n".join(story_lines)

# ---------------------------
# HTML report (data story above charts)
# ---------------------------

def generate_risk_matrix_html(df: pd.DataFrame) -> str:
    display_df = df[["Country","Total Distinct Entities","Distinct Individuals","Distinct Non-Individuals",
                     "Rating - Personal & Non-Personal","Rating - Personal","Rating - Non-Personal"]].copy()

    def base_color(val): return "background-color: #c9edff; text-align:center;"
    def risk_color(val): return f"background-color: {RISK_COLOR_MAP.get(val, '#FFFFFF')}; text-align:center; color:black;"

    styled = (
        display_df.style
        .map(base_color, subset=["Country","Total Distinct Entities","Distinct Individuals","Distinct Non-Individuals"])
        .map(risk_color, subset=["Rating - Personal & Non-Personal","Rating - Personal","Rating - Non-Personal"])
        .set_table_styles([{"selector": "th", "props": [("background-color","#1f4e78"),("color","white"),("font-weight","bold")]}])
    )
    return styled.to_html(escape=False, index=False)

def generate_ofac_risk_report(df: pd.DataFrame, export_path: Optional[str]=None) -> Tuple[str, go.Figure]:
    """
    Returns HTML content and the heatmap figure.
    The data story is embedded ABOVE the charts (as requested).
    """
    # create html pieces
    data_story_html = generate_data_story(df)
    html_table = generate_risk_matrix_html(df)
    heatmap_fig = generate_risk_heatmap(df)
    heatmap_html = heatmap_fig.to_html(full_html=False, include_plotlyjs="cdn")

    html_content = f"""
    <html>
    <head>
      <title>OFAC Country Risk Report</title>
      <meta charset="utf-8"/>
      <style>
        body {{ font-family: Arial, Helvetica, sans-serif; margin: 20px; }}
        h1,h2,h3 {{ color: #1f4e78; }}
        .story {{ margin-bottom: 20px; padding: 10px; border-left: 4px solid #1f4e78; background:#f7fbfd }}
        footer {{ margin-top: 40px; font-size: 13px; color: #333; }}
        a {{ color: #1f4e78; text-decoration: none; }}
      </style>
    </head>
    <body>
      <h1>OFAC Country Risk Matrix Report</h1>

      <!-- Data story (above charts) -->
      <div class="story">
        {data_story_html}
      </div>

      <h2>Data Metrics & Risk Ratings</h2>
      {html_table}

      <h2>Interactive Risk Heatmap</h2>
      {heatmap_html}

      <footer>
        Developed by Atsu Vovor | Data & Analytics |
        <a href="https://atsuvovor.github.io/projects_portfolio.github.io/">GitHub</a> |
        <a href="https://www.linkedin.com/in/atsu-vovor-mmai-9188326/">LinkedIn</a> |
        <a href="https://public.tableau.com/app/profile/atsu.vovor8645/vizzes">Tableau Portfolio</a>
      </footer>
    </body>
    </html>
    """

    if export_path:
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    return html_content, heatmap_fig
