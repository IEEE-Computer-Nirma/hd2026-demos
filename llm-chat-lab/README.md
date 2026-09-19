# LLM Chat Lab

A plug-and-play project with two components: a **chat platform** powered by Meta's Llama via Snowflake Cortex, and a **custom ML model** trained on 2.7M real FEMA flood insurance claims.

---

## Architecture

```
llm-chat-lab/
├── streamlit_app.py          # Chat UI — Llama 3.1 70B via Cortex COMPLETE
├── snowflake.yml             # Workspace Streamlit manifest
├── .streamlit/config.toml    # Dark theme
├── ml/
│   └── train_flood_claim_model.py   # Train RandomForest on FEMA data
└── sql/
    └── setup.sql             # Create ML feature table from public data
```

```
                    ┌─────────────────────────┐
  User prompt  ──►  │   Streamlit Chat UI     │
                    │   (streamlit_app.py)     │
                    └────────┬────────────────┘
                             │
                    SNOWFLAKE.CORTEX.COMPLETE()
                             │
                    ┌────────▼────────────────┐
                    │   Llama 3.1-70B         │
                    │   (Snowflake-hosted)     │
                    └─────────────────────────┘

  ┌──────────────────────────────────────────────────────┐
  │  ML Pipeline (separate)                              │
  │                                                      │
  │  FEMA_NATIONAL_FLOOD_INSURANCE_PROGRAM_CLAIM_INDEX   │
  │  (2.7M claims, SNOWFLAKE_PUBLIC_DATA_FREE)           │
  │        │                                             │
  │        ▼  sql/setup.sql                              │
  │  FLOOD_CLAIM_FEATURES (engineered feature table)     │
  │        │                                             │
  │        ▼  ml/train_flood_claim_model.py              │
  │  RandomForest classifier (scikit-learn)              │
  │  Predicts: cause of flood damage                     │
  └──────────────────────────────────────────────────────┘
```

---

## Part A: Chat Platform

A minimal, functional chat app using **Llama 3.1-70B** through `SNOWFLAKE.CORTEX.COMPLETE`.

### Features

- Multi-turn conversation with full history
- Configurable temperature and max token sliders
- Quick-prompt buttons in the sidebar
- Dark theme UI
- Zero external dependencies — runs entirely in Snowflake Workspace
- ~100 lines of code

### How it works

1. User types a message in the Streamlit chat input
2. The app builds a conversation array (system prompt + message history)
3. Calls `SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b', ...)` with the prompt
4. Displays the streamed response in the chat window

No API keys, no PATs, no external services. The Snowflake session handles auth.

### Changing the model

Edit line 12 in `streamlit_app.py`:

```python
MODEL = "llama3.1-70b"  # Options: llama3.1-8b, llama3.1-405b, mistral-large2, claude-sonnet-4-5
```

---

## Part B: Custom ML Model

A **Random Forest classifier** trained on real-world FEMA National Flood Insurance Program (NFIP) claim data to predict the **cause of flood damage**.

### Dataset

| Property | Value |
|----------|-------|
| Source | `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_NATIONAL_FLOOD_INSURANCE_PROGRAM_CLAIM_INDEX` |
| Total rows | ~2.7 million claims |
| Training sample | 200,000 rows (stratified) |
| Free? | Yes — included with every Snowflake account |

### Target classes (4)

| Class | Description | % of data |
|-------|-------------|-----------|
| Accumulation of rainfall or snowmelt | Surface water flooding from rain/snow | ~45% |
| Tidal water overflow | Coastal/storm surge flooding | ~26% |
| Stream, river, or lake overflow | Riverine flooding | ~21% |
| Other causes | Wind-driven rain, sewer backup, etc. | ~8% |

### Features (24 total)

**Numeric (17):**
- Water depth (ft), water duration (hrs)
- Property value, damage amount, contents value, contents damage
- Insurance coverage, contents coverage, deductible
- Elevation difference, damage ratio, coverage ratio
- Latitude, longitude
- Loss month, loss year, building age (years)

**Categorical (7):**
- Occupancy type (single family, condo, etc.)
- Number of floors, building type
- Replacement cost basis, flood zone
- Basement/enclosure type, state

### Model

| Parameter | Value |
|-----------|-------|
| Algorithm | RandomForestClassifier (scikit-learn) |
| Trees | 200 |
| Max depth | 20 |
| Min samples leaf | 10 |
| Class weighting | Balanced |
| Train/test split | 80/20, stratified |

### What the model learns

The model captures real-world patterns like:
- **Coastal claims** (tidal overflow) cluster at low elevation near coastlines
- **Rainfall flooding** dominates in inland areas and peaks in spring/summer
- **River overflow** correlates with higher water depth and duration
- **Building age and flood zone** are strong predictors of cause type

---

## Setup

### Prerequisites

- A Snowflake account (free trial works)
- Access to `SNOWFLAKE_PUBLIC_DATA_FREE` (auto-imported for all accounts)
- A warehouse (e.g., `COMPUTE_WH`)

### Step 1: Launch the chat app (no setup needed)

The Streamlit chat app works independently — no database or ML setup required.

1. Open the workspace containing this project in Snowsight
2. Open `streamlit_app.py` in the file tree
3. Click **Run** in the top-right corner of the editor
4. The app launches with a chat interface — type a message and hit Enter

The app calls `SNOWFLAKE.CORTEX.COMPLETE` with Llama 3.1-70B. All auth is handled by the Snowflake session.

### Step 2: Create the ML feature table

This step is only needed if you want to train the flood claim model.

1. Open a **SQL worksheet** in Snowsight (not a Python file)
2. Open `sql/setup.sql` and run it — takes ~30 seconds on an XS warehouse
3. This creates database `LLM_CHAT_LAB_DB` with schema `ML` and table `FLOOD_CLAIM_FEATURES` (~2.4M rows)

### Step 3: Train the model

`ml/train_flood_claim_model.py` is a **Python script**, not a Streamlit app. Run it as a Python file:

1. Open `ml/train_flood_claim_model.py` in the workspace file tree
2. Make sure you are running it as a **Python file** (not via the Streamlit Run button)
3. Click **Run** — the script executes top-to-bottom and prints results to the output pane
4. Training takes ~2 minutes on an XS warehouse and prints:
   - Test accuracy and classification report
   - Confusion matrix
   - Top 10 feature importances
   - A demo prediction
5. The model artifact is saved to `/tmp/flood_claim_model.pkl`

> **Note:** If `train_flood_claim_model.py` launches as a Streamlit app instead of running as Python, check that `ml/` is **not** listed under `artifacts` in `snowflake.yml`.

---

## Cost

| Component | Estimated credits |
|-----------|-------------------|
| Feature table creation (XS warehouse, ~30s) | ~0.01 |
| Model training (XS warehouse, ~2 min) | ~0.03 |
| Chat (per message, Llama 3.1-70B) | ~0.001 |

Total to run the entire project end-to-end: **under 0.05 credits**.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Chat model | Llama 3.1-70B (Snowflake Cortex) |
| Chat UI | Streamlit |
| ML framework | scikit-learn (RandomForest) |
| Data | FEMA NFIP Claims (2.7M rows, free) |
| Compute | Snowflake Warehouse |
| Auth | Snowflake session (zero config) |

---

## License

MIT
