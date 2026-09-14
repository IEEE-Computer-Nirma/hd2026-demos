@echo off
REM setup.bat — One-command setup for the US Macro Economic Observatory (Windows)

echo ============================================
echo  US Macro Economic Observatory - Local Setup
echo ============================================
echo.

REM 1. Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is required but not found on PATH.
    echo Install Python 3.9+ from https://www.python.org/downloads/
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VERSION=%%v
echo [1/5] Found Python %PY_VERSION%

REM 2. Create virtual environment
if not exist "venv" (
    echo [2/5] Creating virtual environment...
    python -m venv venv
) else (
    echo [2/5] Virtual environment already exists.
)

REM 3. Activate and install
echo [3/5] Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt -q

REM 4. Set up secrets
if not exist ".streamlit\secrets.toml" (
    echo [4/5] Creating .streamlit\secrets.toml from template...
    copy .streamlit\secrets.toml.example .streamlit\secrets.toml >nul
    echo.
    echo   *** ACTION REQUIRED ***
    echo   Edit .streamlit\secrets.toml with your Snowflake credentials:
    echo     - account:   Your Snowflake account identifier
    echo     - user:      Your Snowflake username
    echo     - password:  Your Snowflake password
    echo     - role:      A role with access to SNOWFLAKE_PUBLIC_DATA_FREE
    echo     - warehouse: An active warehouse (default: COMPUTE_WH)
    echo.
) else (
    echo [4/5] .streamlit\secrets.toml already exists - skipping.
)

REM 5. Done
echo [5/5] Setup complete!
echo.
echo To run the app:
echo   1. Edit .streamlit\secrets.toml with your Snowflake credentials
echo   2. Activate the virtual environment:
echo        venv\Scripts\activate
echo   3. Start the app:
echo        streamlit run streamlit_app.py
echo.
echo The app will open at http://localhost:8501
