###########################
# pivot_risk_visuals.py
# Author: Atsu Vovor
# Date: 2025-11-09
###########################
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import risk_report_generator as rg
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
    IS_STREAMLIT_CLOUD
)

def map_risk_score_to_level(score: float) -> str:
    """
    Convert a numeric Avg_Risk_Score into its qualitative risk level.
    """
    if pd.isna(score):
        return "Unknown"
    if score < 1.5:
        return "Low"
    elif score < 2.5:
        return "Medium Low"
    elif score < 3.5:
        return "Medium"
    elif score < 4.5:
        return "Medium High"
    elif score < 5.5:
        return "High"
    else:
        return "Critical"

def add_risk_level_and_colors(pivot_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Risk_Level column based on Avg_Risk_Score (numeric) and apply risk color logic
    for both Avg_Risk_Score and Risk_Level columns for Streamlit display.
    """

    if "Avg_Risk_Score" not in pivot_df.columns:
        return pivot_df, pivot_df.style  # fail-safe

    df = pivot_df.copy()

    # Define mapping thresholds (based on numeric Avg_Risk_Score)
    def map_score_to_level(score: float) -> str:
        if score >= 5.5:
            return "Critical"
        elif score >= 4.5:
            return "High"
        elif score >= 3.5:
            return "Medium High"
        elif score >= 2.5:
            return "Medium"
        elif score >= 1.5:
            return "Medium Low"
        else:
            return "Low"

    df["Risk_Level"] = df["Avg_Risk_Score"].apply(map_score_to_level)

    # Color formatting function
    def color_risk(val):
        if val in RISK_COLOR_MAP:
            return f"background-color: {RISK_COLOR_MAP[val]}; color: white; font-weight: bold;"
        try:
            # If numeric, infer its level then color
            level = map_score_to_level(val)
            return f"background-color: {RISK_COLOR_MAP[level]}; color: white; font-weight: bold;"
        except Exception:
            return ""

    # Apply style to both columns
    df_styled = (
        df.style
        .applymap(color_risk, subset=["Avg_Risk_Score"])
        .applymap(color_risk, subset=["Risk_Level"])
    )

    return df, df_styled

#----
def prepare_pivot_data(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate SDNs by Country and Sanctions Program (drop SDN_Type splitting) and compute average risk score."""
    required_cols = ["Country", "Sanctions Program"]
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"Missing required column: {c}")

    # If dataset is huge, limit to essential columns to save memory
    cols_to_use = [c for c in ["Country", "Sanctions Program", "ent_num", "Risk_Score"] if c in df.columns]
    df = df[cols_to_use].copy()

    # Ensure Risk_Score exists
    if "Risk_Score" not in df.columns:
        # use lightweight aggregation without exploding combinations
        agg = (
            df.groupby(["Country", "Sanctions Program"], observed=True)["ent_num"]
            .nunique()
            .reset_index(name="Total_SDNs")
        )
        agg["Avg_Risk_Score"] = agg["Total_SDNs"].apply(
            lambda x: 1 if x <= 200 else (2 if x <= 400 else (3 if x <= 600 else (4 if x <= 800 else (5 if x <= 1000 else 6))))
        )
        pivot_df = agg
    else:
        pivot_df = (
            df.groupby(["Country", "Sanctions Program"], observed=True)
            .agg(
                Total_SDNs=("ent_num", "nunique"),
                Avg_Risk_Score=("Risk_Score", "mean"),
            )
            .reset_index()
        )

    # Round risk score
    pivot_df["Avg_Risk_Score"] = pivot_df["Avg_Risk_Score"].round(1)

    # If dataframe is still too large, truncate for visualization safety
    if len(pivot_df) > 20000:
        pivot_df = pivot_df.sample(20000, random_state=42)
        print("[prepare_pivot_data] Pivot truncated to 20k rows for performance safety.")

    return pivot_df


def generate_program_heatmap(pivot_df: pd.DataFrame) -> go.Figure:
    """Heatmap showing average risk score across country-program combinations."""
    # use pivot_table to avoid duplicate index errors
    pivot_heat = pivot_df.pivot_table(index="Country", columns="Sanctions Program", values="Avg_Risk_Score", aggfunc="mean", fill_value=0, observed=False)

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot_heat.values,
            x=pivot_heat.columns,
            y=pivot_heat.index,
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
            colorbar=dict(
                title="Risk Level (Score)",
                tickvals=[1,2,3,4,5,6],
                ticktext=["Low","Med Low","Medium","Med High","High","Critical"]
            ),
            xgap=2,  # white border width between cells
            ygap=2,
            hovertemplate="<b>%{y}</b><br>Program: %{x}<br>Avg Risk Score: %{z}<extra></extra>",
        )
    )
    rg._annotate_heatmap(fig, pivot_heat.values, pivot_heat.columns, pivot_heat.index, font_size=11)
    fig.update_layout(
        title="Cross-Border Sanctions Program Risk Concentration",
        xaxis_title="Sanctions Program",
        yaxis_title="Country",
        height=600
    )
    return fig

def generate_program_bar_chart(pivot_df: pd.DataFrame, selected_country=None, selected_program=None) -> go.Figure:
    filtered_df = pivot_df.copy()
    subtitle = ""
    if selected_country:
        filtered_df = filtered_df[filtered_df["Country"] == selected_country]
        subtitle += f" — {selected_country}"
    if selected_program:
        filtered_df = filtered_df[filtered_df["Sanctions Program"] == selected_program]
        subtitle += f" — {selected_program}"

    fig = px.bar(
        filtered_df,
        x="Country",
        y="Total_SDNs",
        color="Sanctions Program",
        title=f"SDN Concentration by Sanctions Program and Country{subtitle}",
    )
    #fig.update_layout(xaxis_tickangle=-45, yaxis_title="Total SDNs", height=900, legend_title="Sanctions Program", transition_duration=500)
    # Enable stacked bar mode
    fig.update_layout(
        barmode="stack",
        xaxis_tickangle=-45,
        yaxis_title="Total SDNs",
        height=600,
        margin=dict(t=70)
    )
    return fig

def generate_risk_donut_chart(filtered_df: pd.DataFrame, selected_country=None, selected_program=None) -> go.Figure:
    if filtered_df.empty:
        return go.Figure()
    risk_counts = filtered_df["Risk_Level"].value_counts().reset_index()
    risk_counts.columns = ["Risk_Level", "Count"]
    fig = px.pie(risk_counts, names="Risk_Level", values="Count", color="Risk_Level", color_discrete_map=RISK_COLOR_MAP, hole=0.5,
                 title=f"Risk Rating Distribution — {selected_country or 'All'} / {selected_program or 'All'}")
    fig.update_traces(textinfo="percent+label", pull=[0.05]*len(risk_counts))
    fig.update_layout(showlegend=True, height=400)
    return fig
