import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Search


# -----------------------
# Helper: cached geocoding
# -----------------------
@st.cache_data(show_spinner=False)
def geocode_countries(countries: list[str]) -> pd.DataFrame:
    geolocator = Nominatim(user_agent="ofac_dashboard")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    
    map_data = []
    for country in countries:
        if country != "Unknown":
            try:
                location = geocode(country)
                if location:
                    map_data.append({
                        "Country": country,
                        "lat": location.latitude,
                        "lon": location.longitude
                    })
            except Exception as e:
                # optionally log error
                pass
    return pd.DataFrame(map_data)
    
# -----------------------------------------------------------
# 🌎 Geographical SDN Risk Map (Folium + Google Maps + Search)
# -----------------------------------------------------------
def render_geo_sdn_risk_map(pv_pivot_df_full, RISK_SCORE_MAP, RISK_COLOR_MAP):
    """
    Renders an interactive Folium map showing SDN risk distribution globally.
    Integrates multiple basemaps (Google Maps, OSM, CartoDB) and fixes known geocoding issues.
    Adds a country search bar for quick navigation.
    """

    with st.expander("🌎 Geographical SDN Risk Map (SDN Volume, Risk Level, Top 3 Programs)"):
        if pv_pivot_df_full.empty:
            st.info("Pivot data is empty — cannot render geographical map.")
            return

        # --- Basemap selection
        basemap_options = {
            "🗺️ CartoDB Positron (default)": "CartoDB positron",
            "🌍 OpenStreetMap": "OpenStreetMap",
            "🛰️ Google Satellite": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            "⛰️ Google Terrain": "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}"
        }

        basemap_choice = st.selectbox("Select map style:", list(basemap_options.keys()), index=0)
        tile_url = basemap_options[basemap_choice]
        tile_attr = "Google" if "google" in tile_url.lower() else "OpenStreetMap / CartoDB"

        df = pv_pivot_df_full.copy()
        sdn_col_candidates = [c for c in ['Total_SDNs', 'Entity Count', 'SDN_Count'] if c in df.columns]
        sdn_col = sdn_col_candidates[0] if sdn_col_candidates else None

        if sdn_col is None or 'Sanctions Program' not in df.columns or 'Country' not in df.columns:
            st.info("Pivot missing required columns ('Country', 'Sanctions Program', '<Total SDN count column>'). Cannot render map.")
            return

        # --- Aggregation
        country_sdn = df.groupby('Country')[sdn_col].sum().reset_index(name='Total_SDNs')
        country_risk = df.groupby('Country')['Avg_Risk_Score'].mean().reset_index(name='Avg_Risk_Score')

        prog_agg = (
            df.groupby(['Country', 'Sanctions Program']).agg(
                SDN_Count=(sdn_col, 'sum'),
                Program_Avg_Risk=('Avg_Risk_Score', 'mean')
            ).reset_index()
        )

        # --- Risk label mapping
        def program_risk_label(score):
            try:
                nearest = min(RISK_SCORE_MAP.values(), key=lambda v: abs(v - score))
                return [k for k, v in RISK_SCORE_MAP.items() if v == nearest][0]
            except Exception:
                return 'Unknown'

        RISK_EMOJI_MAP = {'Low': '🟢', 'Moderate': '🟡', 'High': '🟠', 'Critical': '🔴', 'Unknown': '⚪'}

        prog_agg['Risk_Label'] = prog_agg['Program_Avg_Risk'].apply(program_risk_label)
        prog_agg['Emoji'] = prog_agg['Risk_Label'].map(lambda x: RISK_EMOJI_MAP.get(x, '⚪'))

        prog_agg = prog_agg.sort_values(['Country', 'SDN_Count'], ascending=[True, False])
        top3 = prog_agg.groupby('Country').head(3)
        top3['Prog_Hover'] = top3.apply(
            lambda r: f"{r['Emoji']} {r['Sanctions Program']} (SDNs: {int(r['SDN_Count'])}) — {r['Risk_Label']}",
            axis=1
        )
        top3_str = top3.groupby('Country')['Prog_Hover'].apply(lambda arr: '<br>'.join(arr)).reset_index(name='Top3_Programs_Detail')

        map_df = country_sdn.merge(country_risk, on='Country', how='left').merge(top3_str, on='Country', how='left')

        # --- Manual coordinate fixes
        manual_coords = {
            "North Korea": {"lat": 40.3399, "lon": 127.5101},
            "West Bank": {"lat": 31.9466, "lon": 35.3027},
            "Gaza Strip": {"lat": 31.4167, "lon": 34.3333},
            "Ivory Coast": {"lat": 7.539989, "lon": -5.54708},
            "Kosovo": {"lat": 42.6026, "lon": 20.9030},
            "Taiwan": {"lat": 23.6978, "lon": 120.9605},
            "Palestine": {"lat": 31.9522, "lon": 35.2332},
        }

        # --- Geocode & filter
        countries_to_geocode = [c for c in map_df['Country'].dropna().unique().tolist() if c != 'Unknown']
        geo_df = geocode_countries(countries_to_geocode) if countries_to_geocode else pd.DataFrame()

        geo_df = geo_df[~geo_df["Country"].isin(["Northern Gaza", "North Korea"])]
        geo_df = geo_df.drop_duplicates(subset=["Country"], keep="last")

        # Apply manual overrides
        for country, coords in manual_coords.items():
            if not geo_df.empty and country in geo_df["Country"].values:
                geo_df.loc[geo_df["Country"] == country, ["lat", "lon"]] = coords["lat"], coords["lon"]
            else:
                geo_df = pd.concat([
                    geo_df,
                    pd.DataFrame([{"Country": country, "lat": coords["lat"], "lon": coords["lon"]}])
                ], ignore_index=True)

        map_df = map_df.merge(geo_df, on='Country', how='left')

        # --- Risk color mapping
        def score_to_label(x):
            try:
                nearest = min(RISK_SCORE_MAP.values(), key=lambda v: abs(v - x))
                return [k for k, v in RISK_SCORE_MAP.items() if v == nearest][0]
            except Exception:
                return 'Unknown'

        map_df['Risk_Level'] = map_df['Avg_Risk_Score'].apply(score_to_label)
        map_df['Risk_Color'] = map_df['Risk_Level'].map(lambda x: RISK_COLOR_MAP.get(x, 'gray'))

        # --- Folium Map
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

        # Add selected basemap
        if "google" in tile_url.lower():
            folium.TileLayer(tiles=tile_url, attr=tile_attr, name=basemap_choice, overlay=False, control=True).add_to(m)
        else:
            folium.TileLayer(tile_url, attr=tile_attr, name=basemap_choice, overlay=False, control=True).add_to(m)

        # Add extra basemaps
        folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
        folium.TileLayer("CartoDB positron", name="CartoDB Positron").add_to(m)

        # --- Markers layer (for Search)
        marker_layer = folium.FeatureGroup(name="SDN Risk Markers").add_to(m)

        color_map = {'Low': 'green', 'Moderate': 'yellow', 'High': 'orange', 'Critical': 'red', 'Unknown': 'gray'}

        for _, row in map_df.iterrows():
            if pd.notna(row['lat']) and pd.notna(row['lon']):
                color = color_map.get(row['Risk_Level'], 'gray')
                popup_html = f"""
                <b>{row['Country']}</b><br>
                Total SDNs: {int(row['Total_SDNs'])}<br>
                Country Risk: {row['Risk_Level']}<br><br>
                <u>Top 3 Programs</u><br>{row['Top3_Programs_Detail']}
                """
                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=max(4, min(25, row['Total_SDNs'] / 100)),
                    color=color,
                    fill=True,
                    fill_opacity=0.7,
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(marker_layer)

        # --- Add searchable feature
        Search(
            layer=marker_layer,
            search_label="Country",
            placeholder="🔍 Search for a country...",
            collapsed=False
        ).add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)
        st_folium(m, width=1200, height=700)
