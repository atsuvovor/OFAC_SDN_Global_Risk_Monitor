###########################
#data_processor.py
# Author: Atsu Vovor
# Date: 2025-11-09
###########################

from __future__ import annotations
import os
from typing import Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
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

# Constants
JOIN_COLUMN = "ent_num"
SDN_TYPE_COL = "SDN_Type"
COUNTRY_COL = "Country"
SDN_PROGRAM_COLUMN = "Sanctions Program"
MAP_JOIN_COLUMN = "Sanction codes"
MAP_DESCRIPTION_COLUMN = "Active Sanctions Programs"

# -------------------------
# Loading helpers
# -------------------------
def load_csv(file_path: str) -> Optional[pd.DataFrame]:
    if file_path is None:
        return None
    if not os.path.exists(file_path):
        print(f"[load_csv] File not found: {file_path}")
        return None
    try:
        df = pd.read_csv(file_path, encoding="latin-1")
        return df
    except Exception as e:
        print(f"[load_csv] Error reading {file_path}: {e}")
        return None

def load_map_data(map_filepath: str) -> Optional[pd.DataFrame]:
    if map_filepath is None or not os.path.exists(map_filepath):
        print(f"[load_map_data] Map file not found: {map_filepath}")
        return None
    try:
        map_df = pd.read_csv(map_filepath, encoding="latin-1")
        return map_df
    except Exception as e:
        print(f"[load_map_data] Error loading map file: {e}")
        return None

# -------------------------
# Data cleaning helper
# -------------------------
def clean_invalid_countries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace invalid or placeholder Country values like '-0-' with 'Unknown'.
    Keeps all rows but standardizes invalid entries for consistency.
    """
    if "Country" not in df.columns:
        return df

    df = df.copy()
    invalid_mask = df["Country"].astype(str).str.strip() == "-0-"
    replaced_count = invalid_mask.sum()

    if replaced_count > 0:
        df.loc[invalid_mask, "Country"] = "Unknown SDN"
        #print(f"[clean_invalid_countries] Replaced {replaced_count} invalid Country values ('-0-') with 'Unknown'.")

    return df


# -------------------------
# Risk logic
# -------------------------
def apply_risk_rating(value: float) -> str:
    if value <= 200:
        return "Low"
    elif value <= 400:
        return "Medium Low"
    elif value <= 600:
        return "Medium"
    elif value <= 800:
        return "Medium High"
    elif value <= 1000:
        return "High"
    else:
        return "Critical"

# -------------------------
# Compute metrics
# -------------------------
def compute_country_risk_metrics(master_ofac_df: pd.DataFrame) -> pd.DataFrame:
    df = master_ofac_df.copy()
    for c in [JOIN_COLUMN, SDN_TYPE_COL, COUNTRY_COL]:
        if c not in df.columns:
            raise ValueError(f"Input dataframe must contain column '{c}'")

    total = df.groupby(COUNTRY_COL)[JOIN_COLUMN].nunique().rename("Total Distinct Entities")
    inds = df[df[SDN_TYPE_COL].fillna("").str.lower() == "individual"].groupby(COUNTRY_COL)[JOIN_COLUMN].nunique().rename("Distinct Individuals")
    non_inds = df[df[SDN_TYPE_COL].fillna("").str.lower() != "individual"].groupby(COUNTRY_COL)[JOIN_COLUMN].nunique().rename("Distinct Non-Individuals")

    metrics = pd.concat([total, inds, non_inds], axis=1).fillna(0).reset_index()
    metrics["Rating - Personal & Non-Personal"] = metrics["Total Distinct Entities"].apply(apply_risk_rating)
    metrics["Rating - Personal"] = metrics["Distinct Individuals"].apply(apply_risk_rating)
    metrics["Rating - Non-Personal"] = metrics["Distinct Non-Individuals"].apply(apply_risk_rating)

    for col in ["Rating - Personal & Non-Personal", "Rating - Personal", "Rating - Non-Personal"]:
        metrics[f"{col} Color"] = metrics[col].map(RISK_COLOR_MAP)
        metrics[f"{col} Score"] = metrics[col].map(RISK_SCORE_MAP)

    metrics["Total Distinct Entities"] = metrics["Total Distinct Entities"].astype(int)
    metrics["Distinct Individuals"] = metrics["Distinct Individuals"].astype(int)
    metrics["Distinct Non-Individuals"] = metrics["Distinct Non-Individuals"].astype(int)

    return metrics

# -------------------------
# KPI / KRI computation
# -------------------------
def compute_kpis_kris(metrics_df: pd.DataFrame) -> Tuple[Dict[str, Any], Dict[str, Any], pd.DataFrame]:
    total_entities = int(metrics_df["Total Distinct Entities"].sum())
    top_concentration = int(metrics_df["Total Distinct Entities"].max()) if not metrics_df.empty else 0
    critical_count = int((metrics_df["Rating - Personal & Non-Personal"] == "Critical").sum())
    non_ind_total = int(metrics_df["Distinct Non-Individuals"].sum())
    non_ind_ratio = f"{round((non_ind_total / total_entities) * 100, 1)}%" if total_entities > 0 else "0%"

    kpis = {
        "Total Distinct Entities": {"value": total_entities, "tooltip": "Unique sanctioned entities across all jurisdictions."},
        "Top SDN Concentration": {"value": top_concentration, "tooltip": "Highest country SDN count."},
    }
    kris = {
        "Critical Risk Jurisdictions": {"value": critical_count, "tooltip": "Countries flagged as Critical."},
        "Non-Individual Entity Ratio": {"value": non_ind_ratio, "tooltip": "Proportion of non-individual SDNs."},
    }

    # grouped — if metrics_df contains Program/Sdn_Type then create grouped view, otherwise copy
    if all(col in metrics_df.columns for col in ["Country", "Sanctions Program", "SDN_Type", "Total Distinct Entities"]):
        grouped = (
            metrics_df.groupby(["Country", "Sanctions Program", "SDN_Type"])
            .agg(Total_Entities=("Total Distinct Entities", "sum"))
            .reset_index()
        )
    else:
        grouped = metrics_df.copy()

    grouped["Risk_Level"] = grouped["Total Distinct Entities"].apply(apply_risk_rating)
    grouped["Risk_Score"] = grouped["Risk_Level"].map(RISK_SCORE_MAP)
    grouped["Risk_Color"] = grouped["Risk_Level"].map(RISK_COLOR_MAP)
    return kpis, kris, grouped

# -------------------------
# Upstream pivot preparation (FIXED)
# -------------------------
def prepare_pivot_data(master_ofac_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate sanctions data by Country and Sanctions Program,
    collapsing multiple SDN types into a single aggregated row.
    Returns columns: Country, Sanctions Program, SDN_Count, Avg_Risk_Score, Risk_Color
    """
    df = master_ofac_df.copy()
    # Ensure required columns exist
    for c in [JOIN_COLUMN, SDN_PROGRAM_COLUMN, COUNTRY_COL]:
        if c not in df.columns:
            raise ValueError(f"Input dataframe must contain column '{c}'")

    # If Risk_Score not present, compute a simple one from counts
    if "Risk_Score" not in df.columns:
        # create a base count per ent_num per program-country
        # we'll approximate risk score: apply risk rating on counts after grouping
        temp = (
            df.groupby([COUNTRY_COL, SDN_PROGRAM_COLUMN, JOIN_COLUMN])
            .size()
            .reset_index(name="tmp_count")
        )
        agg = temp.groupby([COUNTRY_COL, SDN_PROGRAM_COLUMN]).size().reset_index(name="SDN_Count")
        agg["Risk_Level"] = agg["SDN_Count"].apply(apply_risk_rating)
        agg["Risk_Score"] = agg["Risk_Level"].map(RISK_SCORE_MAP)
        agg["Avg_Risk_Score"] = agg["Risk_Score"].astype(float)
        pivot_df = agg
    else:
        # Use provided Risk_Score and aggregate across SDN_Type to produce one row per Country+Program
        pivot_df = (
            df.groupby([COUNTRY_COL, SDN_PROGRAM_COLUMN])
            .agg(
                SDN_Count=(JOIN_COLUMN, "nunique"),
                Avg_Risk_Score=("Risk_Score", "mean")
            )
            .reset_index()
        )

    # map color
    def risk_color(score):
        if score < 2: return "#2E4A1E"
        elif score < 3: return "#9ACD32"
        elif score < 4: return "#FFFF00"
        elif score < 5: return "#FFA500"
        else: return "#FF0000"

    pivot_df["Avg_Risk_Score"] = pivot_df["Avg_Risk_Score"].round(2)
    pivot_df["Risk_Color"] = pivot_df["Avg_Risk_Score"].apply(risk_color)
    return pivot_df

# -------------------------
# Pipeline
# -------------------------
def run_ofac_data_pipeline(
    sdn_file: Optional[str],
    add_file: Optional[str],
    map_file: Optional[str],
    df_override: Optional[pd.DataFrame] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Returns (metrics_df, aggregated_df, master_df)
    """
    if df_override is not None:
        master_df = df_override.copy()
    else:
        sdn_df = load_csv(sdn_file)
        add_df = load_csv(add_file)
        map_df = load_map_data(map_file)

        if sdn_df is None:
            print("[pipeline] Missing SDN file — aborting.")
            return None, None, None

        if add_df is not None and JOIN_COLUMN in sdn_df.columns and JOIN_COLUMN in add_df.columns:
            master_df = pd.merge(sdn_df, add_df, on=JOIN_COLUMN, how="left")
        else:
            master_df = sdn_df.copy()

        if map_df is not None and SDN_PROGRAM_COLUMN in master_df.columns:
            map_df_renamed = map_df.rename(columns={MAP_JOIN_COLUMN: SDN_PROGRAM_COLUMN})
            master_df = pd.merge(master_df, map_df_renamed, on=SDN_PROGRAM_COLUMN, how="left")

    # 🔹 Clean invalid countries
    master_df = clean_invalid_countries(master_df)

    # Generate base metrics
    metrics_df = compute_country_risk_metrics(master_df)
    _, _, aggregated_df = compute_kpis_kris(metrics_df)
    return metrics_df, aggregated_df, master_df

if __name__ == "__main__":
    # quick test
    df = pd.DataFrame({
        "ent_num": [1,2,3,4,5,6,7,8,9,10],
        "SDN_Type": ["individual","entity","entity","individual","entity","entity","individual","entity","entity","individual"],
        "Country": ["Russia","Russia","Iran","China","Mexico","Mexico","UAE","Colombia","Turkey","Lebanon"],
        "Sanctions Program": ["IRAN","IRAN","RUSSIA","CHINA","MEX","MEX","UAE","COL","TUR","LEB"]
    })
    metrics_df, aggregated_df, master_df = run_ofac_data_pipeline(None, None, None, df_override=df)
    print(metrics_df.head())
