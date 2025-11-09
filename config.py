##############################################################
# config.py
# ------------------------------------------------------------
# Shared configuration for risk logic, color maps, and constants
# used across all modules (pivot_risk_visuals, risk_report_generator, etc.)
##############################################################

RISK_COLOR_MAP = {
    "Low": "#2E4A1E",          # Dark green
    "Medium Low": "#9ACD32",   # Yellow-green
    "Medium": "#FFFF00",       # Yellow
    "Medium High": "#FFA500",  # Orange
    "High": "#FF0000",         # Red
    "Critical": "#800080",     # Purple
}

RISK_SCORE_MAP = {
    "Low": 1,
    "Medium Low": 2,
    "Medium": 3,
    "Medium High": 4,
    "High": 5,
    "Critical": 6,
}
