##############################################################
# Dockerfile for OFAC_SDN_Global_Risk_Monitor
# ------------------------------------------------------------
# Builds a containerized Streamlit dashboard with AI Agent
# integration (Validator + Executive) and RAG capabilities.
#
# Author: Atsu Vovor
# Date: 2025-11-08
##############################################################

# ===============================
# 🐍 1. Base image
# ===============================
FROM python:3.11-slim

# ===============================
# 🧰 2. System dependencies
# ===============================
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ===============================
# 📦 3. Working directory
# ===============================
WORKDIR /app

# ===============================
# 📁 4. Copy project files
# ===============================
COPY . /app

# ===============================
# 📋 5. Install dependencies (Full AI / RAG stack)
# ===============================
RUN pip install --no-cache-dir -r requirements-docker.txt

# ===============================
# ⚙️ 6. Environment variables
# ===============================
ENV IS_DOCKER=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    REPORTS_DIR=/app/reports \
    CACHE_DIR=/app/cache \
    LLM_MODEL_PATH=/app/models/ggml-mistral-7b.Q4_K_M.gguf \
    USE_RAG=true \
    LOG_LEVEL=INFO

# ===============================
# 🚪 7. Expose Streamlit port
# ===============================
EXPOSE 8501

# ===============================
# 🗂️ 8. Volumes for persistent data, reports, and models
# ===============================
VOLUME ["/app/data", "/app/reports", "/app/models"]

# ===============================
# 🚀 9. Run Streamlit app
# ===============================
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
