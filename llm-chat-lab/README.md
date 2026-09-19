# Snowflake Cortex LLM Chat Lab & FEMA Flood ML Pipeline

A plug-and-play project featuring two production-ready components:
1. **Interactive AI Chat Platform**: Multi-turn conversation assistant powered by Snowflake Cortex LLM functions (`llama3.1-70b`, `claude-3-5-sonnet`, `mistral-large2`).
2. **Predictive Machine Learning Pipeline**: Scikit-learn Random Forest classifier trained on 2.7M+ real FEMA National Flood Insurance Program (NFIP) claim records to classify damage causes.

---

## 📋 Table of Contents

1. [Architecture & Workflow](#architecture--workflow)
2. [Prerequisites](#prerequisites)
3. [Component A: Cortex LLM Chat Assistant](#component-a-cortex-llm-chat-assistant)
   - [Running in Snowflake Workspaces (Zero-Config)](#running-in-snowflake-workspaces-zero-config)
   - [Running Locally with Streamlit](#running-locally-with-streamlit)
   - [Configuring LLM Models & Hyperparameters](#configuring-llm-models--hyperparameters)
4. [Component B: FEMA Flood ML Classification Pipeline](#component-b-fema-flood-ml-classification-pipeline)
   - [Step 1: Database & Feature Table Setup (SQL)](#step-1-database--feature-table-setup-sql)
   - [Step 2: Training the Classifier (Python / Snowpark)](#step-2-training-the-classifier-python--snowpark)
   - [Dataset & Feature Specification](#dataset--feature-specification)
   - [Model Architecture & Artifacts](#model-architecture--artifacts)
5. [Complete Step-by-Step Setup Commands](#complete-step-by-step-setup-commands)
6. [Cost & Credit Estimation](#cost--credit-estimation)
7. [Troubleshooting & FAQs](#troubleshooting--faqs)

---

## Architecture & Workflow

```
llm-chat-lab/
├── streamlit_app.py               # Streamlit Chat interface (Cortex COMPLETE)
├── snowflake.yml                  # Snowflake Workspace application manifest
├── pyproject.toml                 # Workspace dependencies (Streamlit in Snowflake)
├── .streamlit/
│   └── config.toml                # UI theme configuration
├── ml/
│   └── train_flood_claim_model.py # Random Forest ML training pipeline (Snowpark + scikit-learn)
└── sql/
    └── setup.sql                  # Feature engineering DDL from public FEMA dataset
```

```
                     ┌──────────────────────────────────────┐
   User Message ───► │ Streamlit Chat App (streamlit_app.py)│
                     └──────────────────┬───────────────────┘
                                        │
                     SNOWFLAKE.CORTEX.COMPLETE()
                                        │
                     ┌──────────────────▼───────────────────┐
                     │ Llama 3.1-70B / Claude 3.5 Sonnet    │
                     │ (Snowflake Native AI Engine)         │
                     └──────────────────────────────────────┘

   ┌────────────────────────────────────────────────────────────────────────┐
   │ ML PIPELINE WORKFLOW                                                   │
   │                                                                        │
   │ 1. Public Shared Source                                                │
   │    SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE                          │
   │    .FEMA_NATIONAL_FLOOD_INSURANCE_PROGRAM_CLAIM_INDEX (~2.7M rows)       │
   │                             │                                          │
   │                             ▼ (Execute sql/setup.sql)                  │
   │ 2. Feature Table                                                       │
   │    LLM_CHAT_LAB_DB.ML.FLOOD_CLAIM_FEATURES (24 curated features)       │
   │                             │                                          │
   │                             ▼ (Execute ml/train_flood_claim_model.py)  │
   │ 3. Model Training & Export                                             │
   │    Scikit-learn RandomForest Classifier (Saved to /tmp/flood_claim.pkl)│
   └────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

Before running the application or ML training script, ensure you have:
* A **Snowflake Account** with `ACCOUNTADMIN` or developer privileges (Free Trial accounts supported).
* **`SNOWFLAKE_PUBLIC_DATA_FREE`** imported into your account from Snowflake Marketplace.
* A standard virtual warehouse (e.g., `COMPUTE_WH`).
* **Python 3.10, 3.11, or 3.12+** installed (if running locally or executing standalone scripts).

---

## Component A: Cortex LLM Chat Assistant

The chat application (`streamlit_app.py`) leverages Snowflake Cortex LLMs with zero external API key management.

### Running in Snowflake Workspaces (Zero-Config)

1. Open **Snowsight** at [app.snowflake.com](https://app.snowflake.com).
2. Go to **Projects** > **Workspaces**.
3. Open the workspace folder `llm-chat-lab/`.
4. Open `streamlit_app.py` in the editor.
5. In the top bar, ensure `COMPUTE_WH` warehouse is selected.
6. Click the **Run** button in the upper-right corner.

The app uses the native active session identity (`st.connection("snowflake")`) with zero credential setup.

---

### Running Locally with Streamlit

If you prefer developing on your local machine:

#### 1. Setup Virtual Environment & Dependencies
```bash
# Navigate to project directory
cd llm-chat-lab

# Create virtual environment
python3 -m venv .venv

# Activate environment
# macOS / Linux:
source .venv/bin/activate
# Windows (PowerShell):
# .\.venv\Scripts\Activate.ps1

# Install requirements
pip install --upgrade pip
pip install "streamlit>=1.35.0" "snowflake-connector-python>=3.8.0" "snowflake-snowpark-python>=1.15.0"
```

#### 2. Configure Local Snowflake Connection (`.streamlit/secrets.toml`)
Create `.streamlit/secrets.toml` in your project folder:

```toml
[connections.snowflake]
account = "YOUR_ACCOUNT_IDENTIFIER"      # e.g., "XY12345" or "org-account"
user = "YOUR_SNOWFLAKE_USERNAME"
password = "YOUR_SNOWFLAKE_PASSWORD"
role = "ACCOUNTADMIN"
warehouse = "COMPUTE_WH"
database = "LLM_CHAT_LAB_DB"
schema = "ML"
```

#### 3. Start Streamlit App
```bash
streamlit run streamlit_app.py
```
Open your browser at `http://localhost:8501`.

---

### Configuring LLM Models & Hyperparameters

To switch between Cortex models, edit line 14 in `streamlit_app.py`:

```python
MODEL = "llama3.1-70b"  # Available options: "llama3.1-70b", "llama3.1-8b", "llama3.1-405b", "mistral-large2", "claude-3-5-sonnet"
```

---

## Component B: FEMA Flood ML Classification Pipeline

### Step 1: Database & Feature Table Setup (SQL)

Run the feature extraction DDL to create `LLM_CHAT_LAB_DB.ML.FLOOD_CLAIM_FEATURES`. Open a SQL Worksheet in Snowsight and execute:

```sql
-- 1. Create target Database and Schema
CREATE DATABASE IF NOT EXISTS LLM_CHAT_LAB_DB;
USE DATABASE LLM_CHAT_LAB_DB;

CREATE SCHEMA IF NOT EXISTS ML;
USE SCHEMA ML;

-- 2. Materialize and engineer features from FEMA public dataset (~2.4M rows)
CREATE OR REPLACE TABLE FLOOD_CLAIM_FEATURES AS
WITH raw AS (
    SELECT
        CAUSE_OF_DAMAGE,
        OCCUPANCY_TYPE,
        NUMBER_OF_FLOORS,
        BUILDING_TYPE,
        FLOOD_WATER_DEPTH,
        FLOOD_WATER_DURATION_HOURS,
        BUILDING_PROPERTY_VALUE,
        BUILDING_DAMAGE_AMOUNT,
        CONTENTS_PROPERTY_VALUE,
        CONTENTS_DAMAGE_AMOUNT,
        TOTAL_BUILDING_INSURANCE_COVERAGE,
        TOTAL_CONTENTS_INSURANCE_COVERAGE,
        BUILDING_DEDUCTIBLE,
        CONTENTS_DEDUCTIBLE,
        REPLACEMENT_COST_BASIS,
        CURRENT_FLOOD_ZONE,
        BASEMENT_ENCLOSURE_CRAWLSPACE,
        DATE_OF_LOSS,
        ORIGINAL_CONSTRUCTION_DATE,
        LATITUDE,
        LONGITUDE,
        STATE_GEO_ID,
        ELEVATION_DIFFERENCE,
        BASE_FLOOD_ELEVATION
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE
         .FEMA_NATIONAL_FLOOD_INSURANCE_PROGRAM_CLAIM_INDEX
    WHERE CAUSE_OF_DAMAGE IN (
        'Accumulation of rainfall or snowmelt',
        'Tidal water overflow',
        'Stream, river, or lake overflow',
        'Other causes'
    )
    AND BUILDING_DAMAGE_AMOUNT IS NOT NULL
    AND BUILDING_PROPERTY_VALUE IS NOT NULL
    AND BUILDING_PROPERTY_VALUE > 0
)
SELECT
    -- Target
    CAUSE_OF_DAMAGE                                          AS DAMAGE_CAUSE,

    -- Property Categorical Features
    OCCUPANCY_TYPE,
    NUMBER_OF_FLOORS,
    BUILDING_TYPE,
    REPLACEMENT_COST_BASIS,
    CURRENT_FLOOD_ZONE,
    COALESCE(BASEMENT_ENCLOSURE_CRAWLSPACE, 'Unknown')       AS BASEMENT_TYPE,

    -- Numeric Features
    COALESCE(FLOOD_WATER_DEPTH, 0)                           AS WATER_DEPTH_FT,
    COALESCE(FLOOD_WATER_DURATION_HOURS, 0)                  AS WATER_DURATION_HRS,
    BUILDING_PROPERTY_VALUE                                   AS PROPERTY_VALUE,
    BUILDING_DAMAGE_AMOUNT                                    AS DAMAGE_AMOUNT,
    COALESCE(CONTENTS_PROPERTY_VALUE, 0)                     AS CONTENTS_VALUE,
    COALESCE(CONTENTS_DAMAGE_AMOUNT, 0)                      AS CONTENTS_DAMAGE,
    COALESCE(TOTAL_BUILDING_INSURANCE_COVERAGE, 0)           AS INSURANCE_COVERAGE,
    COALESCE(TOTAL_CONTENTS_INSURANCE_COVERAGE, 0)           AS CONTENTS_COVERAGE,
    COALESCE(BUILDING_DEDUCTIBLE, 0)                         AS DEDUCTIBLE,
    COALESCE(ELEVATION_DIFFERENCE, 0)                        AS ELEVATION_DIFF,

    -- Engineered Financial Ratios
    ROUND(BUILDING_DAMAGE_AMOUNT / NULLIF(BUILDING_PROPERTY_VALUE, 0), 4) AS DAMAGE_RATIO,
    ROUND(COALESCE(TOTAL_BUILDING_INSURANCE_COVERAGE, 0) / NULLIF(BUILDING_PROPERTY_VALUE, 0), 4) AS COVERAGE_RATIO,

    -- Geospatial & Temporal Features
    COALESCE(LATITUDE, 0)                                    AS LAT,
    COALESCE(LONGITUDE, 0)                                   AS LON,
    COALESCE(STATE_GEO_ID, 'Unknown')                        AS STATE_GEO,
    EXTRACT(MONTH FROM DATE_OF_LOSS)                         AS LOSS_MONTH,
    EXTRACT(YEAR FROM DATE_OF_LOSS)                          AS LOSS_YEAR,
    DATEDIFF('year', COALESCE(ORIGINAL_CONSTRUCTION_DATE, DATE_OF_LOSS), DATE_OF_LOSS) AS BUILDING_AGE_YRS

FROM raw
WHERE BUILDING_DAMAGE_AMOUNT >= 0
  AND DAMAGE_AMOUNT <= BUILDING_PROPERTY_VALUE * 5;

-- 3. Verify row counts and distribution
SELECT DAMAGE_CAUSE, COUNT(*) AS CLAIM_COUNT
FROM LLM_CHAT_LAB_DB.ML.FLOOD_CLAIM_FEATURES
GROUP BY DAMAGE_CAUSE
ORDER BY CLAIM_COUNT DESC;
```

---

### Step 2: Training the Classifier (Python / Snowpark)

#### In Snowflake Workspaces
1. In the file tree, click on `ml/train_flood_claim_model.py`.
2. Select warehouse `COMPUTE_WH`.
3. Click **Run** (as a Python script).
4. The output pane will stream the training progress and evaluation metrics.

#### Locally via Terminal
```bash
# Ensure dependencies are installed
pip install scikit-learn pandas numpy snowflake-snowpark-python joblib

# Run the training script
python ml/train_flood_claim_model.py
```

---

### Dataset & Feature Specification

| Metric | Details |
|--------|---------|
| **Source Dataset** | `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_NATIONAL_FLOOD_INSURANCE_PROGRAM_CLAIM_INDEX` |
| **Total Available Records** | ~2,700,000 claims |
| **Training Sample Size** | 200,000 stratified samples (configurable in script) |
| **Target Variable** | `DAMAGE_CAUSE` (4 classes: Rainfall/Snowmelt, Tidal Overflow, River/Stream Overflow, Other) |
| **Feature Count** | 24 features (17 continuous numeric + ratios, 7 categorical) |

---

### Model Architecture & Artifacts

| Parameter | Specification |
|-----------|---------------|
| **Estimator** | `sklearn.ensemble.RandomForestClassifier` |
| **Number of Estimators (`n_estimators`)** | 200 trees |
| **Tree Depth (`max_depth`)** | 20 |
| **Min Samples Leaf** | 10 |
| **Class Weighting** | `balanced` |
| **Evaluation Split** | 80% Train / 20% Test (Stratified) |
| **Saved Model Location** | `/tmp/flood_claim_model.pkl` |

---

## Complete Step-by-Step Setup Commands

Here is the quick-copy sequence of commands to set up the entire project from a clean environment:

```bash
# 1. Clone repository
git clone https://github.com/IEEE-Computer-Nirma/hd2026-demos.git
cd hd2026-demos/llm-chat-lab

# 2. Setup Python environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install packages
pip install --upgrade pip
pip install -r requirements.txt || pip install streamlit snowflake-connector-python snowflake-snowpark-python scikit-learn pandas numpy

# 4. Launch Streamlit Chat
streamlit run streamlit_app.py

# 5. Train Flood Model
python ml/train_flood_claim_model.py
```

---

## Cost & Credit Estimation

| Operation | Warehouse Size | Duration | Est. Credits |
|-----------|----------------|----------|--------------|
| SQL Feature Extraction (`setup.sql`) | X-Small (XS) | ~30 seconds | ~0.008 credits |
| ML Training Script (`train_flood_claim_model.py`) | X-Small (XS) | ~2 minutes | ~0.033 credits |
| Cortex Chat Queries (Llama 3.1-70B) | Serverless | Instant | ~0.001 credits/query |

Total end-to-end testing cost is **less than 0.05 Snowflake credits**.

---

## Troubleshooting & FAQs

### 1. `Table 'SNOWFLAKE_PUBLIC_DATA_FREE...FEMA_...' does not exist`
* **Solution**: You must add the free dataset from Snowflake Marketplace. Go to **Marketplace** > search `Snowflake Public Data Free` > click **Get**.

### 2. `Invalid model name: llama3.1-70b` or `Cortex function execution error`
* **Solution**: Ensure your account region supports Snowflake Cortex AI functions. If `llama3.1-70b` is restricted in your region, update `MODEL = "mistral-large2"` or `MODEL = "llama3.1-8b"` in `streamlit_app.py`.

### 3. `train_flood_claim_model.py` opens in Streamlit UI instead of executing as a Python script
* **Solution**: Ensure `ml/` is not included in the `artifacts` section of `snowflake.yml`. Run it using the Python script execution runner in Snowflake Workspaces or locally via `python ml/train_flood_claim_model.py`.

---

## License

MIT License
