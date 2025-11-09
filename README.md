# 📊 OFAC SDN Global Risk Monitor

The **OFAC SDN Global Risk Monitor** is an interactive compliance analytics dashboard designed for rapid assessment of sanctions risk across jurisdictions.  
It integrates **Python data analytics**, **Streamlit interactive dashboards**, and **AI-driven insights** for executive reporting.

---

## ℹ️ About the Project

---

# 📊 OFAC SDN Global Risk Monitor: Compliance Analytics Dashboard

The **OFAC SDN Global Risk Monitor** is an interactive data visualization project designed to empower compliance and financial risk teams with rapid, quantifiable assessment of sanctions exposure.  
This solution analyzes *Specially Designated Nationals (SDNs)* data to highlight geographic concentration and entity type exposure across key jurisdictions.  
It leverages Python’s data stack and Streamlit’s interactive capabilities for efficient reporting and compliance monitoring.

---

### 🔬 Analytical Core: Risk Calculation & Logic

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

### 🔝 Key Performance & Risk Indicators (KPI/KRI)

| Indicator | Type | Definition and Business Insight |
| :--- | :--- | :--- |
| **Total Distinct Entities** | **KPI** | Count of unique sanctioned entities across jurisdictions — measures total sanctions volume. |
| **Critical Risk Jurisdictions** | **KRI** | Number of countries flagged as *Critical* — indicates top compliance priorities. |
| **Non-Individual Entity Ratio** | **KRI** | Percentage of organizations or vessels (non-individuals) among SDNs — highlights systemic exposure. |
| **Top SDN Concentration** | **KPI** | The highest total count of entities per country, defining concentration risk ceiling. |

---

### 📂 Data Sources

| File Name | Description |
| :--- | :--- |
| **sdn.csv** | Core SDN entity data including names, SDN Type (Individual/Non-Individual), and sanction program details. |
| **add.csv** | Supplementary address data linked by `ent_num`, providing country-level geographic context. |

---

### 🛠️ Technology Stack

The **Python + Streamlit** implementation of the OFAC Risk Dashboard modernizes the original Excel-based model into a fully automated, interactive web application.  
It integrates data cleansing, dynamic risk modeling, and executive reporting — providing a scalable and intelligent platform for sanctions risk monitoring and analytics.

| Component                         | Technology Used                                  | Function                                                                                                                                                                                                                                                     |
| :-------------------------------- | :----------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Data Integration & ETL**        | **Pandas**                                       | Reads, cleans, and merges the `sdn.csv`, `add.csv`, and `map.csv` datasets on the common key (`ent_num`). Handles invalid or missing country values, applies normalization, and maintains referential integrity between entity and address records.          |
| **Risk Modeling & Calculation**   | **Custom Python Logic (Risk Scoring Functions)** | Implements rule-based risk scoring through defined thresholds using `apply_risk_rating()`. Generates `Risk_Level` and `Risk_Score` columns based on SDN entity volumes per country and sanction program.                                                     |
| **Visualization & Interactivity** | **Plotly Express + Streamlit UI Components**     | Provides dynamic, interactive charts (heatmaps, bar charts, and distributions) with filters for program and country selection, toggle between aggregation types, and detailed tooltips. Uses Streamlit for responsive layout and real-time user interaction. |
| **Automated Reporting**           | **FPDF + HTML Export**                           | Generates downloadable executive-style reports in both PDF and HTML formats, embedding visualizations, legends, and dynamically generated data stories summarizing key business insights.                                                                    |
| **AI-Driven Insights (Optional)** | **GPT-based Narrative Generator**                | Produces an adaptive “Data Story” section summarizing risk concentration, top jurisdictions, and actionable compliance insights based on filtered data selections.    

---

## 🏗️ Architecture Overview

### Diagram

![OFAC SDN Global Risk Monitor Architecture](ofac_sdn_readme_diagram.png)

### Textual Description

1. **GitHub Repository**
   - Stores all project files: `app.py`, `config.py`, `ai_agent/`, `requirements*.txt`, etc.  
   - Serves as the source for both Streamlit Cloud and Docker deployments.

2. **Streamlit Cloud (Lightweight Deployment)**
   - Uses `requirements.txt` for core dependencies only.  
   - Provides a **web-accessible dashboard** for data visualization and executive summaries.  
   - Excludes heavy AI / RAG libraries to ensure smooth cloud deployment.

3. **Docker Cloud / Local Docker (Full AI Deployment)**
   - Uses `requirements-docker.txt` for full AI stack including **ValidatorAgent**, **ExecutiveAgent**, **RAG**, and LLM support.  
   - Allows **persistent volumes** for:
     - `/app/data` → CSVs and OFAC datasets  
     - `/app/reports` → PDFs and executive summaries  
     - `/app/models` → LLMs and FAISS embeddings  
   - Enables scalable AI-driven insight generation, data validation, and RAG-powered reporting.

4. **AI Workflow Inside Docker**
   - **ValidatorAgent** validates CSV structure and checks data quality.  
   - **ExecutiveAgent** generates **dashboard insights and executive reports**, leveraging **RAG retrieval** from FAISS vector stores and LLM embeddings.  
   - Streamlit dashboards are updated dynamically with validated data and AI-generated insights.

---
Absolutely! Here’s a **ready-to-use `README.md`** script for your `OFAC_SDN_Global_Risk_Monitor` project. This combines all your content—`ABOUT_MARKDOWN`, architecture diagram, deployment instructions, AI agent workflow, and folder structure—into a single, professional README file.

You can save this directly as `README.md` in your GitHub repository:

````markdown
# 📊 OFAC SDN Global Risk Monitor

The **OFAC SDN Global Risk Monitor** is an interactive compliance analytics dashboard designed for rapid assessment of sanctions risk across jurisdictions.  
It integrates **Python data analytics**, **Streamlit interactive dashboards**, and **AI-driven insights** for executive reporting.

---

## ℹ️ About the Project

# 📊 OFAC SDN Global Risk Monitor: Compliance Analytics Dashboard

The **OFAC SDN Global Risk Monitor** is an interactive data visualization project designed to empower compliance and financial risk teams with rapid, quantifiable assessment of sanctions exposure.  
This solution analyzes *Specially Designated Nationals (SDNs)* data to highlight geographic concentration and entity type exposure across key jurisdictions.  
It leverages Python’s data stack and Streamlit’s interactive capabilities for efficient reporting and compliance monitoring.

---

### 🔬 Analytical Core: Risk Calculation & Logic

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

### 🔝 Key Performance & Risk Indicators (KPI/KRI)

| Indicator | Type | Definition and Business Insight |
| :--- | :--- | :--- |
| **Total Distinct Entities** | **KPI** | Count of unique sanctioned entities across jurisdictions — measures total sanctions volume. |
| **Critical Risk Jurisdictions** | **KRI** | Number of countries flagged as *Critical* — indicates top compliance priorities. |
| **Non-Individual Entity Ratio** | **KRI** | Percentage of organizations or vessels (non-individuals) among SDNs — highlights systemic exposure. |
| **Top SDN Concentration** | **KPI** | The highest total count of entities per country, defining concentration risk ceiling. |

---

### 📂 Data Sources

| File Name | Description |
| :--- | :--- |
| **sdn.csv** | Core SDN entity data including names, SDN Type (Individual/Non-Individual), and sanction program details. |
| **add.csv** | Supplementary address data linked by `ent_num`, providing country-level geographic context. |

---

### 🛠️ Technology Stack

The **Python + Streamlit** implementation of the OFAC Risk Dashboard modernizes the original Excel-based model into a fully automated, interactive web application.  
It integrates data cleansing, dynamic risk modeling, and executive reporting — providing a scalable and intelligent platform for sanctions risk monitoring and analytics.

| Component                         | Technology Used                                  | Function                                                                                                                                                                                                                                                     |
| :-------------------------------- | :----------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Data Integration & ETL**        | **Pandas**                                       | Reads, cleans, and merges the `sdn.csv`, `add.csv`, and `map.csv` datasets on the common key (`ent_num`). Handles invalid or missing country values, applies normalization, and maintains referential integrity between entity and address records.          |
| **Risk Modeling & Calculation**   | **Custom Python Logic (Risk Scoring Functions)** | Implements rule-based risk scoring through defined thresholds using `apply_risk_rating()`. Generates `Risk_Level` and `Risk_Score` columns based on SDN entity volumes per country and sanction program.                                                     |
| **Visualization & Interactivity** | **Plotly Express + Streamlit UI Components**     | Provides dynamic, interactive charts (heatmaps, bar charts, and distributions) with filters for program and country selection, toggle between aggregation types, and detailed tooltips. Uses Streamlit for responsive layout and real-time user interaction. |
| **Automated Reporting**           | **FPDF + HTML Export**                           | Generates downloadable executive-style reports in both PDF and HTML formats, embedding visualizations, legends, and dynamically generated data stories summarizing key business insights.                                                                    |
| **AI-Driven Insights (Optional)** | **GPT-based Narrative Generator**                | Produces an adaptive “Data Story” section summarizing risk concentration, top jurisdictions, and actionable compliance insights based on filtered data selections.    

---

## 🏗️ Architecture Overview

### Diagram

![OFAC SDN Global Risk Monitor Architecture](ofac_sdn_readme_diagram.png)

### Textual Description

1. **GitHub Repository**
   - Stores all project files: `app.py`, `config.py`, `ai_agent/`, `requirements*.txt`, etc.  
   - Serves as the source for both Streamlit Cloud and Docker deployments.

2. **Streamlit Cloud (Lightweight Deployment)**
   - Uses `requirements.txt` for core dependencies only.  
   - Provides a **web-accessible dashboard** for data visualization and executive summaries.  
   - Excludes heavy AI / RAG libraries to ensure smooth cloud deployment.

3. **Docker Cloud / Local Docker (Full AI Deployment)**
   - Uses `requirements-docker.txt` for full AI stack including **ValidatorAgent**, **ExecutiveAgent**, **RAG**, and LLM support.  
   - Allows **persistent volumes** for:
     - `/app/data` → CSVs and OFAC datasets  
     - `/app/reports` → PDFs and executive summaries  
     - `/app/models` → LLMs and FAISS embeddings  
   - Enables scalable AI-driven insight generation, data validation, and RAG-powered reporting.

4. **AI Workflow Inside Docker**
   - **ValidatorAgent** validates CSV structure and checks data quality.  
   - **ExecutiveAgent** generates **dashboard insights and executive reports**, leveraging **RAG retrieval** from FAISS vector stores and LLM embeddings.  
   - Streamlit dashboards are updated dynamically with validated data and AI-generated insights.

---

## 🚀 Quick Start Guide

### Streamlit Cloud Deployment (Lightweight)

```bash
# 1. Clone repo
git clone https://github.com/your-username/OFAC_SDN_Global_Risk_Monitor.git
cd OFAC_SDN_Global_Risk_Monitor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run dashboard
streamlit run app.py
````

### Docker Cloud / Local Docker Deployment (Full AI/RAG)

```bash
# 1. Build Docker image
docker build -t ofac_sdn_risk_monitor:latest -f Dockerfile .

# 2. Run container with persistent volumes
docker run -p 8501:8501 \
  -v /local/data:/app/data \
  -v /local/reports:/app/reports \
  -v /local/models:/app/models \
  ofac_sdn_risk_monitor:latest

# 3. Access dashboard
# http://localhost:8501
```

---

## 📂 File Structure

```
OFAC_SDN_Global_Risk_Monitor/
│
├── .github/                 # CI/CD workflows for Docker
├── app.py                   # Streamlit dashboard entry point
├── config.py                # Shared configuration (risk logic, colors, constants)
├── data_processor.py        # Data processing and ETL logic
├── risk_report_generator.py # PDF/HTML reporting & visualization logic
├── ai_agent/                # AI agents, prompts, and RAG utilities
├── data/                    # CSV input files (sdn.csv, add.csv)
├── reports/                 # Generated PDFs & summaries
├── models/                  # LLM & embeddings
├── requirements.txt         # Lightweight dependencies for Streamlit
├── requirements-docker.txt  # Full dependencies for Docker + AI
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🌐 Deployment Links

* **GitHub Repository:** [Your GitHub Repo Link Here]
* **Streamlit Cloud App:** [Your Streamlit Cloud URL Here]

---

## 🤖 AI Agent Integration

* **ValidatorAgent**: Validates uploaded datasets and checks data quality.
* **ExecutiveAgent**: Generates insights and executive reports using **RAG + LLMs**.
* Supports real-time dashboards and PDF executive summaries.
* Volumes `/app/models`, `/app/data`, and `/app/reports` ensure persistence of models, datasets, and outputs.

---

## ⚙️ Environment Variables (Docker)

| Variable                | Description                         | Default                                 |
| ----------------------- | ----------------------------------- | --------------------------------------- |
| `IS_DOCKER`             | Indicates containerized environment | true                                    |
| `STREAMLIT_SERVER_PORT` | Streamlit server port               | 8501                                    |
| `DATA_DIR`              | CSV input folder                    | /app/data                               |
| `REPORTS_DIR`           | Output folder for PDFs              | /app/reports                            |
| `CACHE_DIR`             | Temporary cache folder              | /app/cache                              |
| `LLM_MODEL_PATH`        | Path to LLM inside container        | /app/models/ggml-mistral-7b.Q4_K_M.gguf |
| `USE_RAG`               | Enable RAG for ExecutiveAgent       | true                                    |

---

## 📜 License & Credits

*© 2025 Atsu Vovor — Consultant, Data & Analytics | OFAC SDN Risk Monitor Project*

---


## 🚀 Quick Start Guide

### Streamlit Cloud Deployment (Lightweight)

```bash
# 1. Clone repo
git clone https://github.com/your-username/OFAC_SDN_Global_Risk_Monitor.git
cd OFAC_SDN_Global_Risk_Monitor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run dashboard
streamlit run app.py
