##############################################################
# config.py
# ------------------------------------------------------------
# Shared configuration file for the OFAC_SDN_Global_Risk_Monitor project.
# Centralizes constants, model paths, RAG settings, and deployment config.
#
# Used by:
#   - data_processor.py
#   - risk_report_generator.py
#   - ai_agent/*
#   - app.py
#
# Author: Atsu Vovor
# Date: 2025-11-08
##############################################################

import os

# ============================================================
# 📊 RISK CONFIGURATION
# ============================================================
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

# ============================================================
# ⚙️ APP & DEPLOYMENT SETTINGS
# ============================================================

APP_NAME = "OFAC SDN Global Risk Monitor"
APP_VERSION = "1.0.0"

# Default Streamlit page config
STREAMLIT_LAYOUT = "wide"
STREAMLIT_PAGE_ICON = "🌐"

# Where to store uploaded or processed files in Docker/Cloud
DATA_DIR = os.getenv("DATA_DIR", "./data")
REPORTS_DIR = os.getenv("REPORTS_DIR", "./reports")
CACHE_DIR = os.getenv("CACHE_DIR", "./cache")

# ============================================================
# 🤖 AI AGENT CONFIGURATION
# ============================================================

# Default model paths or identifiers
LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH", "models/ggml-mistral-7b.Q4_K_M.gguf")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# RAG (Retrieval-Augmented Generation) toggle
USE_RAG = os.getenv("USE_RAG", "true").lower() == "true"

# Chunking configuration for document embeddings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150))

# AI Agent types
VALIDATOR_AGENT_NAME = "ValidatorAgent"
EXECUTIVE_AGENT_NAME = "ExecutiveAgent"

# ============================================================
# ☁️ DEPLOYMENT ENVIRONMENT FLAGS
# ============================================================

# Used to detect where the app is running
IS_DOCKER = os.getenv("IS_DOCKER", "false").lower() == "true"
IS_STREAMLIT_CLOUD = os.getenv("IS_STREAMLIT_CLOUD", "false").lower() == "true"

# External service endpoints (if using APIs or Drive)
OFAC_DATA_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
GOOGLE_DRIVE_CREDENTIALS_PATH = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH", "./credentials.json")

# ============================================================
# 🧩 LOGGING & DEBUG SETTINGS
# ============================================================
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============================================================
# 🧠 AI PROMPT / CONTEXT SETTINGS
# ============================================================
MAX_TOKEN_LENGTH = int(os.getenv("MAX_TOKEN_LENGTH", 2048))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.3))

# ============================================================
# ✅ VALIDATION CONSTANTS
# ============================================================
EXPECTED_COLUMNS = [
    "Name", "SDN_Type", "Program", "Country", "Entity_Number", "Remarks"
]
