##############################################################
# app.py
# ------------------------------------------------------------
# Streamlit dashboard for OFAC SDN Global Risk Monitor
# Includes AI Agent integration, risk visualizations, and RAG support
# Author: Atsu Vovor
# Date: 2025-11-09
##############################################################

from __future__ import annotations
import os
import streamlit as st
import pandas as pd
import data_processor as dp
import risk_report_generator as rg
import pivot_risk_visuals as pv
from typing import Optional, Tuple
import plotly.express as px
import math
import pycountry
import geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import plotly.express as px

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

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# -----------------------
# Page setup & project paths
# -----------------------
#st.set_page_config(page_title="OFAC SDN Global Risk Monitor", layout="wide", page_icon="🌍")

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(
    page_title=APP_NAME,
    layout=STREAMLIT_LAYOUT,
    page_icon=STREAMLIT_PAGE_ICON
)



# -----------------------
# Tabs
# -----------------------
tab1, tab2, tab3 = st.tabs(["📈 Dashboard", "ℹ️ About the Dashboard", "📘 Data Dictionary"])

# -----------------------
# Helper: load metrics (cached)
# -----------------------
@st.cache_data
def load_metrics(uploaded_file: Optional[st.runtime.uploaded_file_manager.UploadedFile] = None, use_defaults: bool = True) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Returns (metrics_df, aggregated_df, master_df)
    """
    try:
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            return dp.run_ofac_data_pipeline(None, None, None, df_override=df)
        elif use_defaults and os.path.exists(SDN_PATH):
            return dp.run_ofac_data_pipeline(
                SDN_PATH,
                ADD_PATH if os.path.exists(ADD_PATH) else None,
                MAP_PATH if os.path.exists(MAP_PATH) else None,
            )
        else:
            return None, None, None
    except Exception as e:
        st.error(f"Error loading metrics: {e}")
        return None, None, None

# -----------------------
# Cached helpers for Top-N filtering & heavy computations
# -----------------------
@st.cache_data
def get_country_totals(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Return metrics_df (Total Distinct Entities by country) sorted desc.
    Expecting metrics_df already has "Country" and "Total Distinct Entities".
    """
    if metrics_df is None or metrics_df.empty:
        return pd.DataFrame(columns=["Country", "Total Distinct Entities"])
    return metrics_df[["Country", "Total Distinct Entities"]].dropna().sort_values("Total Distinct Entities", ascending=False).reset_index(drop=True)

@st.cache_data
def get_program_totals(master_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute total distinct entities by Sanctions Program from master_df.
    """
    if master_df is None or master_df.empty or "Sanctions Program" not in master_df.columns:
        return pd.DataFrame(columns=["Sanctions Program", "Total Distinct Entities"])
    grouped = (
        master_df.groupby("Sanctions Program")["ent_num"]
        .nunique()
        .reset_index(name="Total Distinct Entities")
        .sort_values("Total Distinct Entities", ascending=False)
        .reset_index(drop=True)
    )
    return grouped

@st.cache_data
def prepare_filtered_master(master_df: pd.DataFrame, top_countries: list[str], top_programs: list[str]) -> pd.DataFrame:
    """
    Return subset of master_df that is limited to top_countries and top_programs.
    If either list is empty, it will not filter on that dimension.
    """
    if master_df is None or master_df.empty:
        return pd.DataFrame()
    df = master_df.copy()
    if top_countries:
        df = df[df["Country"].isin(top_countries)]
    if top_programs and "Sanctions Program" in df.columns:
        df = df[df["Sanctions Program"].isin(top_programs)]
    return df

@st.cache_data
def prepare_pivot_and_heatmap_df(filtered_master: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare pivot DataFrame used by pv.prepare_pivot_data or pv.generate_program_heatmap.
    This is cached to avoid recompute.
    """
    if filtered_master is None or filtered_master.empty:
        return pd.DataFrame()
    return pv.prepare_pivot_data(filtered_master)

@st.cache_data
def generate_heatmap_figure(pivot_df: pd.DataFrame, agg_option: str = "Mean"):
    """
    Generate heatmap figure (Plotly) using the pivot_df.
    """
    if pivot_df is None or pivot_df.empty:
        return None
    # If Sum is requested, convert Avg_Risk_Score to SDN_Count if available
    tmp = pivot_df.copy()
    if agg_option == "Sum" and ("SDN_Count" in tmp.columns):
        tmp["Avg_Risk_Score"] = tmp["SDN_Count"]
    # polar: delegate to rg/pv generator
    fig = pv.generate_program_heatmap(tmp)
    return fig

@st.cache_data
def generate_program_bar(pivot_df: pd.DataFrame, selected_country: Optional[str] = None, selected_program: Optional[str] = None):
    if pivot_df is None or pivot_df.empty:
        return None
    return pv.generate_program_bar_chart(pivot_df, selected_country, selected_program)

@st.cache_data
def generate_other_charts(df_vis: pd.DataFrame):
    """
    Generate and return other figures used across the app (donut, stacked, percent stacked, risk heatmap).
    Cached to reduce re-computation on reruns where df_vis unchanged.
    """
    return {
        "donut": rg.generate_donut_chart(df_vis) if not df_vis.empty else None,
        "stacked": rg.generate_stacked_bar(df_vis) if not df_vis.empty else None,
        "percent_stacked": rg.generate_percent_stacked(df_vis) if not df_vis.empty else None,
        "risk_heatmap": rg.generate_risk_heatmap(df_vis) if not df_vis.empty else None,
    }

    
# -----------------------
# TAB 1 — Dashboard
# -----------------------
with tab1:
    st.title("🌍 OFAC SDN Global Risk Monitor")
    st.write("***(Interactive OFAC Sanctions Compliance Analytics Dashboard - Risk Ranking, Network Visualization, and Entity Linkage Analysis.)***")

    # Sidebar controls
    st.sidebar.header("Data & Filters")
    uploaded = st.sidebar.file_uploader("Upload master OFAC CSV (must include ent_num, SDN_Type, Country)", type=["csv"])
    use_defaults = st.sidebar.checkbox("Use default CSV files from project folder", value=True)

    # Load metrics + master DF
    metrics_df, agg_df, master_df = load_metrics(uploaded, use_defaults)
    if metrics_df is None or metrics_df.empty or master_df is None or master_df.empty:
        st.warning("No metrics available. Upload a valid master CSV or ensure default CSVs exist in the project folder.")
        st.stop()

    # Ensure Country Unknown sorting and Name normalization
    master_df = master_df.copy()
    # If the pipeline has not replaced '-0-' with 'Unknown', do it here as a safeguard:
    if "Country" in master_df.columns:
        master_df["Country"] = master_df["Country"].astype(str).str.strip().replace({"-0-": "Unknown"})
        # make Unknown appear last in categorical sorting (keeps charts tidy)
        ordered_cats = sorted([c for c in master_df["Country"].unique() if c != "Unknown"])
        if "Unknown" in master_df["Country"].unique():
            ordered_cats.append("Unknown")
        master_df["Country"] = pd.Categorical(master_df["Country"], categories=ordered_cats, ordered=True)

    if "SDN_Name" in master_df.columns and "Name" not in master_df.columns:
        master_df["Name"] = master_df["SDN_Name"]

    # -----------------------
    # Multi-select filters (Programs & Countries) with Select/Deselect All
    # -----------------------
    st.sidebar.subheader("Visual Filters")

    # Program options (from master)
    program_options = sorted(master_df["Sanctions Program"].dropna().unique().tolist()) if "Sanctions Program" in master_df.columns else []
    if not program_options:
        program_options = ["(No Program)"]

    # Select / Deselect All control for programs
    programs_select_all = st.sidebar.checkbox("Select all programs", value=True, key="prog_select_all")
    programs_clear = st.sidebar.checkbox("Clear program selection", value=False, key="prog_clear")
    if programs_clear:
        selected_programs = []
    elif programs_select_all:
        selected_programs = program_options.copy()
    else:
        selected_programs = st.sidebar.multiselect(
            "Sanctions Program (multi-select)",
            options=program_options,
            default=program_options,
            key="program_multiselect"
        )

    # Country options (from metrics_df)
    country_options = sorted(metrics_df["Country"].dropna().unique().tolist()) if "Country" in metrics_df.columns else []
    if not country_options:
        country_options = ["(No Country)"]

    countries_select_all = st.sidebar.checkbox("Select all countries", value=True, key="country_select_all")
    countries_clear = st.sidebar.checkbox("Clear country selection", value=False, key="country_clear")
    if countries_clear:
        selected_countries = []
    elif countries_select_all:
        selected_countries = country_options.copy()
    else:
        selected_countries = st.sidebar.multiselect(
            "Country (multi-select)",
            options=country_options,
            default=country_options,
            key="country_multiselect"
        )

    # Top N controls for charts & pivot (dropdowns)
    st.sidebar.markdown("### Top-N Filters (performance)")
    top_n_options = [5, 10, 20, 30, 50]
    default_country_top = 10 if len(metrics_df) >= 10 else max(3, len(metrics_df))
    top_n_country = st.sidebar.selectbox("Top N Countries (by Total Distinct Entities)", top_n_options, index=top_n_options.index(default_country_top) if default_country_top in top_n_options else 1)
    program_totals_df = get_program_totals(master_df)
    default_program_top = 10 if len(program_totals_df) >= 10 else max(3, len(program_totals_df))
    top_n_program = st.sidebar.selectbox("Top N Sanctions Programs (by Total Distinct Entities)", top_n_options, index=top_n_options.index(default_program_top) if default_program_top in top_n_options else 1)

    # Heatmap aggregation toggle
    agg_option = st.sidebar.radio("Heatmap aggregation", ["Mean", "Sum"], index=0)

    # -----------------------
    # Apply filters to metrics and master
    # -----------------------
    # df_vis is the dataset used for the top-level charts & data story (apply selected countries/programs + top N country limit)
    df_vis = metrics_df.copy()

    if selected_countries:
        df_vis = df_vis[df_vis["Country"].isin(selected_countries)]
    if selected_programs and "Sanctions Program" in df_vis.columns:
        try:
            df_vis = df_vis[df_vis["Sanctions Program"].isin(selected_programs)]
        except Exception:
            pass

    # restrict to top N countries for the main visuals (if column exists)
    if "Total Distinct Entities" in df_vis.columns:
        df_vis = df_vis.nlargest(top_n_country, "Total Distinct Entities")

    # -----------------------
    # KPI / KRI
    # -----------------------
    kpis, kris, grouped = dp.compute_kpis_kris(metrics_df)
    kpi_cols = st.columns(4)
    merged = {**kpis, **kris}
    for i, (label, info) in enumerate(merged.items()):
        with kpi_cols[i % 4]:
            st.metric(label=label, value=info["value"])
            st.caption(info["tooltip"])

    st.markdown("---")

    # -----------------------
    # Data Story (above charts) — dynamic with filtered df_vis
    # -----------------------
    st.markdown("### 🧠 Data Story (Auto-generated)")
    # regenerate story based on df_vis (note: rg.generate_data_story should be reasonably fast)
    story_html = rg.generate_data_story(df_vis)
    st.components.v1.html(story_html, height=400, scrolling=True)

    st.markdown("---")

    # -----------------------
    # Charts (large) — use df_vis for top-level charts
    # -----------------------
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Total Distinct Entities")
        donut_fig = rg.generate_donut_chart(df_vis)
        if donut_fig is not None:
            st.plotly_chart(donut_fig, use_container_width=True)
    with c2:
        st.subheader("SDN Distribution (Stacked)")
        stacked_fig = rg.generate_stacked_bar(df_vis)
        if stacked_fig is not None:
            st.plotly_chart(stacked_fig, use_container_width=True)

    c3, c4 = st.columns([1.3, 1.7])
    with c3:
        st.subheader("SDN Distribution (%)")
        percent_fig = rg.generate_percent_stacked(df_vis)
        if percent_fig is not None:
            st.plotly_chart(percent_fig, use_container_width=True)
    with c4:
        st.subheader("Country Risk Heatmap")
        risk_heatmap_fig = rg.generate_risk_heatmap(df_vis)
        if risk_heatmap_fig is not None:
            st.plotly_chart(risk_heatmap_fig, use_container_width=True)

    st.markdown("---")

    # -----------------------
    # Master data sample
    # -----------------------
    st.subheader("📋 Master Data Sample")
    safe_sample = master_df.head(20).astype(str)
    st.dataframe(safe_sample, use_container_width=True)

    # -----------------------
    # Program-level pivot: use Top-N filtered master_df (both top countries & top programs)
    # -----------------------
    # Determine top lists
    country_totals_df = get_country_totals(metrics_df)
    top_countries = country_totals_df.head(top_n_country)["Country"].tolist() if not country_totals_df.empty else []
    program_totals_df = get_program_totals(master_df)
    top_programs = program_totals_df.head(top_n_program)["Sanctions Program"].tolist() if not program_totals_df.empty else []

    # Allow additional manual multi-select (respect earlier selected_programs / selected_countries)
    # Combine Top-N with the manual selections (if manual selections exist, intersect with Top-N to avoid empty sets)
    # If user manually selected specific programs/countries, prefer the manual selection intersection with top lists
    if selected_programs and selected_programs != program_options:
        # intersect with top_programs to keep size small (if intersection empty, fall back to selected_programs)
        intersection = [p for p in selected_programs if p in top_programs]
        chosen_programs = intersection if intersection else selected_programs
    else:
        chosen_programs = top_programs

    if selected_countries and selected_countries != country_options:
        intersection = [c for c in selected_countries if c in top_countries]
        chosen_countries = intersection if intersection else selected_countries
    else:
        chosen_countries = top_countries

    # Prepare filtered master dataset (cached)
    filtered_master_df = prepare_filtered_master(master_df, chosen_countries, chosen_programs)

    st.markdown("### 🧩 Sanctions Program Aggregation")
    pv_pivot_df = prepare_pivot_and_heatmap_df(filtered_master_df)

    # program bar uses pivot df (cached generator)
    bar_fig = generate_program_bar(pv_pivot_df)
    if bar_fig is not None:
        st.plotly_chart(bar_fig, use_container_width=True)

    # Heavy heatmap generation — put inside an expander and cache
    with st.expander(f"Generate Program × Country Heatmap (Top {len(chosen_countries)} countries × Top {len(chosen_programs)} programs)"):
        st.write("Heatmap aggregation:", agg_option)
        heatmap_fig = generate_heatmap_figure(pv_pivot_df, agg_option)
        if heatmap_fig is not None:
            st.plotly_chart(heatmap_fig, use_container_width=True)
        else:
            st.info("No data available to generate heatmap for the selected Top-N filters.")

    # -----------------------
    # Report preview & export (HTML and PDF)
    # -----------------------
    st.markdown("---")
    st.header("📊 OFAC SDN Risk Report")

    # Generate and preview the report
    report_html, story_text = rg.generate_ofac_risk_report(df_vis)
    st.components.v1.html(report_html, height=800, scrolling=True)

    # Create a temporary directory safely
    #temp_dir = tempfile.mkdtemp()
    #pdf_path = os.path.join(temp_dir, "ofac_risk_report.pdf")

    # -----------------------
    # Export buttons ( HTML)
    # -----------------------
 
    html_content, _ = rg.generate_ofac_risk_report(df_vis)
    st.download_button(
        label="⬇️ Download HTML report",
        data=html_content,
        file_name="ofac_risk_report.html",
        mime="text/html"
    )


    # -----------------------
    # Interactive Pivot — Dropdowns for Country & Program
    # -----------------------
    st.markdown("---")
    st.header("Interactive Pivot Table — Program & Cross-Border Risk Analysis")

    # Prepare pivot from full master_df
    pv_pivot_df_full = pv.prepare_pivot_data(master_df)

   
    # -----------------------------------
    # Interactive Top N Pivot Table View
    # -----------------------------------
    st.markdown("### 📊 Top N Sanctions by Total SDNs")

    # Dropdown for Top N selection
    top_n = st.selectbox(
        "Select Top N Rows to Display:",
        options=[5, 10, 15, 20, 25, 30],
        index=1,
        key="top_n_selector"
    )

    # Enrich dataframe with risk levels and colors
    pv_pivot_df_full, pv_pivot_df_styled = pv.add_risk_level_and_colors(pv_pivot_df_full)

    # Sort by Total_SDNs and display top N
    top_n_df = pv_pivot_df_full.sort_values(by="Total_SDNs", ascending=False).head(top_n)
    # Re-apply styling only to the filtered data (so colors stay consistent)
    _, top_n_styled = pv.add_risk_level_and_colors(top_n_df)

    # Display final interactive top N styled table
    st.dataframe(top_n_styled)

    # Limit pivot rows for performance
    max_rows_for_interactive = 100
    if len(pv_pivot_df_full) > max_rows_for_interactive:
        st.info(f"Pivot has {len(pv_pivot_df_full)} rows. Showing top {max_rows_for_interactive} by Total_SDNs.")
        pv_pivot_df_full = pv_pivot_df_full.sort_values("Total_SDNs", ascending=False).head(max_rows_for_interactive)

    # -----------------------
    # Dropdowns for selecting country & program
    # -----------------------
    st.markdown("### 🔍 View SDN Risk Insights")

    if not pv_pivot_df_full.empty:
        # Create two equal-width columns
        col1, col2 = st.columns(2)

        with col1:
            selected_country = st.selectbox(
                "Select Country",
                options=pv_pivot_df_full["Country"].unique(),
                index=0,
                key="country_select"
            )
            
        with col2:    
            selected_program = st.selectbox(
                "Select Sanctions Program",
                options=pv_pivot_df_full["Sanctions Program"].unique(),
                index=0,
                key="interactive_sanctions_program_select"
            )

        # -----------------------
        # Show risk insights for selected cell
        # -----------------------
        cell = pv_pivot_df_full[
            (pv_pivot_df_full["Country"] == selected_country) &
            (pv_pivot_df_full["Sanctions Program"] == selected_program)
        ]

        if not cell.empty:
            avg_risk_score = cell["Avg_Risk_Score"].values[0]

            # Determine risk level from nearest score
            nearest_score = min(RISK_SCORE_MAP.values(), key=lambda x: abs(x - avg_risk_score))
            risk_level = [k for k, v in RISK_SCORE_MAP.items() if v == nearest_score][0]

            st.write(f"**Country:** {selected_country}")
            st.write(f"**Sanctions Program:** {selected_program}")
            st.write(f"**Average Risk Score:** {avg_risk_score:.2f}")
            st.write(f"**Risk Level:** {risk_level}")

            # Filter SDNs from master_df
            filtered_df_view = master_df[
                (master_df["Country"] == selected_country) &
                (master_df["Sanctions Program"] == selected_program)
            ][["Name", "SDN_Type", "Country", "Sanctions Program","Definition","Active Sanctions Programs"]].drop_duplicates()

            if filtered_df_view.empty:
                st.warning(f"⚠️ No data found for **Country: {selected_country}** and **Program: {selected_program}**.")
            else:
                # Add risk level column
                filtered_df_view["Risk_Level"] = pv.map_risk_score_to_level(avg_risk_score)

                st.dataframe(filtered_df_view.astype(str), use_container_width=True)
                donut_fig = pv.generate_risk_donut_chart(filtered_df_view, selected_country, selected_program)
                if donut_fig is not None:
                    st.plotly_chart(donut_fig, use_container_width=True)
                else:
                    st.info("No pivot data available for SDN insights.")
        else:
             st.warning(f"⚠️ No data found for **Country: {selected_country}** and **Program: {selected_program}**.")
       
        st.caption("""
        Developed by **Atsu Vovor** | Consultant, Data & Analytics  
        Ph: 416-795-8246 | ✉️ atsu.vovor@bell.net  
        [🌐 GitHub](https://atsuvovor.github.io/projects_portfolio.github.io/) | 
        [💼 LinkedIn](https://www.linkedin.com/in/atsu-vovor-mmai-9188326/) | 
        [📊 Tableau Portfolio](https://public.tableau.com/app/profile/atsu.vovor8645/vizzes)  
        
        📍 Mississauga ON   
        
        ### Thank you for visiting!🙏
        """)

# -----------------------
# TAB 2 — About the Dashboard
# -----------------------
with tab2:
    st.markdown(rg.ABOUT_MARKDOWN_INTRO, unsafe_allow_html=True)
    st.image(ARCHITECTURE_PATH, use_container_width=True)
    st.markdown(rg.ABOUT_MARKDOWN_DETAILS, unsafe_allow_html=True)
    st.markdown(rg.ABOUT_MARKDOWN_FOOT, unsafe_allow_html=True)

# -----------------------
# TAB 3 — Data Dictionary
# -----------------------
with tab3:
    st.title("📘 Data Dictionary")
    st.markdown("""
    This section provides a quick **data dictionary** for the dataset used in the dashboard.
    It helps analysts understand field definitions, data types, and missing or unique values.
    """)

    # reload to reflect upload toggles
    metrics_df, agg_df, master_df = load_metrics(uploaded, use_defaults)
    if master_df is None or master_df.empty:
        st.warning("No data available to generate the data dictionary.")
        st.stop()

    # safe sample extraction
    sample_values = []
    for c in master_df.columns:
        non_null = master_df[c].dropna()
        sample = str(non_null.iloc[0]) if not non_null.empty else ""
        sample_values.append(sample)

    dict_df = pd.DataFrame({
        "Column Name": master_df.columns,
        "Data Type": [str(master_df[c].dtype) for c in master_df.columns],
        "Missing Values": [int(master_df[c].isna().sum()) for c in master_df.columns],
        "Unique Values": [int(master_df[c].nunique(dropna=True)) for c in master_df.columns],
        "Sample Value": sample_values,
    })

    descriptions = {
        "ent_num": "Unique identifier linking SDN and Address datasets.",
        "SDN_Name": "Name of the individual or organization under sanctions.",
        "SDN_Type": "Entity type — Individual or Non-Individual.",
        "Sanctions Program": "OFAC sanctions program under which the entity is listed.",
        "Country": "Country or jurisdiction associated with the entity or address.",
        "Address": "Raw address line from add.csv.",
        "Definition": "Program description or definition (from map.csv).",
        "Risk_Level": "Calculated risk rating (Low → Critical).",
    }
    dict_df["Description"] = dict_df["Column Name"].map(descriptions).fillna("")

    st.dataframe(dict_df, use_container_width=True)
    csv_data = dict_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Data Dictionary as CSV", data=csv_data, file_name="data_dictionary.csv", mime="text/csv")
    st.markdown("✅ **Tip:** Use this dictionary as a metadata appendix in audit or compliance documentation.")
