# Snowflake Cortex LLM Chat Application (HackDays Ahmedabad Demo)

A beginner-friendly, step-by-step guide to building and running a simple AI Chat Assistant using Streamlit and Snowflake's Cortex LLM REST API (`claude-3-5-sonnet`, `llama3.1-70b`, `mistral-large2`).

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Clone or Download the Repository](#step-1-clone-or-download-the-repository)
4. [Step 2: Create & Activate Virtual Environment (`venv`)](#step-2-create--activate-virtual-environment-venv)
5. [Step 3: Install Dependencies](#step-3-install-dependencies)
6. [Step 4: Snowflake Account Setup & Personal Access Token (PAT)](#step-4-snowflake-account-setup--personal-access-token-pat)
7. [Step 5: Set Up Snowflake Network Policy (Crucial Step)](#step-5-set-up-snowflake-network-policy-crucial-step)
8. [Step 6: Configure Secrets (`secrets.toml`)](#step-6-configure-secrets-secretstoml)
9. [Step 7: Launch the Application](#step-7-launch-the-application)
10. [Troubleshooting & Common Fixes](#troubleshooting--common-fixes)

---

## Overview

This application connects Streamlit to Snowflake's Cortex REST API to stream response outputs in real-time.

<img width="500" alt="App Example" src="https://github.com/user-attachments/assets/77d46ef8-a4c8-481e-b07c-a81f4c6bbaed" />

---

## Prerequisites

Before starting, ensure you have:
* **Python 3.10, 3.11, or 3.12+** installed on your system. Check your version:
  ```bash
  python --version
  ```
* A **Snowflake Account** (Free Trial accounts work perfectly).

---

## Step 1: Clone or Download the Repository

Open your terminal or command prompt and navigate to your working directory:

```bash
git clone https://github.com/IEEE-Computer-Nirma/hd2026-demos.git
cd hd2026-demos
```

---

## Step 2: Create & Activate Virtual Environment (`venv`)

Creating a virtual environment ensures all project dependencies are isolated and won't conflict with system packages.

### Windows (PowerShell / Command Prompt)

```powershell
# Create virtual environment named '.venv'
python -m venv .venv

# Activate the virtual environment
# In PowerShell:
.\.venv\Scripts\Activate.ps1

# Or in Command Prompt (cmd.exe):
.\.venv\Scripts\activate.bat
```

### macOS / Linux

```bash
# Create virtual environment named '.venv'
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate
```

> **Note:** Once activated, your terminal prompt will show `(.venv)` at the beginning.

---

## Step 3: Install Dependencies

With your virtual environment activated, install the required packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:
* `streamlit` – Interactive web dashboard
* `snowflake-connector-python` – Snowflake database connection
* `sseclient-py` – Server-Sent Events stream parser
* `requests` – HTTP client for Snowflake REST API

---

## Step 4: Snowflake Account Setup & Personal Access Token (PAT)

1. **Sign up for Snowflake** (if you don't have an account):
   Sign up for a trial account at [Snowflake Signup](https://mlh.link/snowflake-signup). Activate your account via email and create a password.
2. **Generate a Personal Access Token (PAT)**:
   * Open your Snowflake console at [app.snowflake.com](https://app.snowflake.com).
   * Navigate to **Settings** -> **Authentication Settings** (or visit [Authentication Settings direct link](https://app.snowflake.com/_deeplink/settings/authentication)).
   * Under **Personal Access Tokens (PAT)**, click **Generate Token**.
   * Copy and safely store the generated API Key.

3. **Find your Account Locator**:
   * Click your user profile in the bottom-left corner of the Snowflake UI.
   * Hover over `Connect a tool to Snowflake` to copy your **Account Identifier** (e.g., `UTYHQNW-MS95509`).

---

## Step 5: Set Up Snowflake Network Policy (Crucial Step)

When using Personal Access Tokens (PAT), Snowflake requires an active **Network Policy** attached to your account or user. Without this step, Snowflake will reject requests with `Fail : Network policy is required.` (Error 390432).

1. In the Snowflake Web UI, go to **Projects** -> **Worksheets** and open a new SQL Worksheet.
2. Set your role in the top-right corner to **`ACCOUNTADMIN`**.
3. Copy and execute the following SQL:

```sql
-- Create an open network policy for development
CREATE OR REPLACE NETWORK POLICY ALLOW_ALL_NP
  ALLOWED_IP_LIST = ('0.0.0.0/0');

-- Apply the policy to your account
ALTER ACCOUNT SET NETWORK_POLICY = ALLOW_ALL_NP;

-- (Optional) Or apply specifically to your user account:
-- ALTER USER YOUR_USERNAME SET NETWORK_POLICY = ALLOW_ALL_NP;
```

---

## Step 6: Configure Secrets (`secrets.toml`)

Create a folder named `.streamlit` in the root directory (if it does not exist) and create a file named `secrets.toml`:

### File Path: `.streamlit/secrets.toml`

```toml
[snowflake]
account = "UTYHQNW-MS95509"
user = "YOUR_SNOWFLAKE_USERNAME"
api_key = "YOUR_PERSONAL_ACCESS_TOKEN_PAT"
role = "ACCOUNTADMIN"
host = "UTYHQNW-MS95509.snowflakecomputing.com"
```

> ⚠️ **Important Host Formatting**:
> Make sure `host` uses your account locator followed by `.snowflakecomputing.com` (e.g., `UTYHQNW-MS95509.snowflakecomputing.com`). Do NOT put your username in the host URL.

---

## Step 7: Launch the Application

Make sure your virtual environment `(.venv)` is activated, then start the Streamlit server:

```bash
streamlit run app.py
```

Or run via Python module:

```bash
python -m streamlit run app.py
```

Your default web browser will automatically open to `http://localhost:8501`.

---

## Troubleshooting & Common Fixes

### 1. `Fail : Network policy is required.` (Error 390432)
* **Cause**: Snowflake PAT authentication requires an active Network Policy on your account.
* **Fix**: Follow [Step 5](#step-5-set-up-snowflake-network-policy-crucial-step) in your Snowflake SQL Worksheet using `ACCOUNTADMIN` role to run `CREATE OR REPLACE NETWORK POLICY ALLOW_ALL_NP ALLOWED_IP_LIST = ('0.0.0.0/0'); ALTER ACCOUNT SET NETWORK_POLICY = ALLOW_ALL_NP;`.

### 2. `AttributeError: st.session_state has no attribute "CONN"`
* **Cause**: Session state accessed `CONN` before connection initialization completed or failed without fallback.
* **Fix**: This has been patched in `app.py`. Ensure `app.py` has initialized `st.session_state.CONN = None` and uses `st.session_state.get("CONN")`.

### 3. `404 Not Found` when sending requests to Snowflake
* **Cause**: Incorrect `host` domain in `.streamlit/secrets.toml`.
* **Fix**: Verify your `host` matches `<account-locator>.snowflakecomputing.com` (e.g. `UTYHQNW-MS95509.snowflakecomputing.com`).

---

## 🛠️ Changing Models

To switch AI models, open `app.py` and modify `MODEL_NAME` around line 18:

```python
MODEL_NAME = "claude-3-5-sonnet" # Options: "claude-3-5-sonnet", "llama3.1-70b", "mistral-large2"
```
