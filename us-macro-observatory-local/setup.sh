#!/usr/bin/env bash
# setup.sh — One-command setup for the US Macro Economic Observatory
set -e

echo "============================================"
echo " US Macro Economic Observatory — Local Setup"
echo "============================================"
echo ""

# 1. Check Python version
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python 3 is required but not found on PATH."
    echo "Install Python 3.9+ from https://www.python.org/downloads/"
    exit 1
fi

PY_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "[1/5] Found $PYTHON_CMD $PY_VERSION"

# 2. Create virtual environment
if [ ! -d "venv" ]; then
    echo "[2/5] Creating virtual environment..."
    $PYTHON_CMD -m venv venv
else
    echo "[2/5] Virtual environment already exists."
fi

# 3. Activate and install dependencies
echo "[3/5] Installing dependencies..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 4. Set up secrets file
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo "[4/5] Creating .streamlit/secrets.toml from template..."
    cp .streamlit/secrets.toml.example .streamlit/secrets.toml
    echo ""
    echo "  *** ACTION REQUIRED ***"
    echo "  Edit .streamlit/secrets.toml with your Snowflake credentials:"
    echo "    - account:   Your Snowflake account identifier"
    echo "    - user:      Your Snowflake username"
    echo "    - password:  Your Snowflake password"
    echo "    - role:      A role with access to SNOWFLAKE_PUBLIC_DATA_FREE"
    echo "    - warehouse: An active warehouse (default: COMPUTE_WH)"
    echo ""
else
    echo "[4/5] .streamlit/secrets.toml already exists — skipping."
fi

# 5. Done
echo "[5/5] Setup complete!"
echo ""
echo "To run the app:"
echo "  1. Edit .streamlit/secrets.toml with your Snowflake credentials"
echo "  2. Activate the virtual environment:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    echo "       venv\\Scripts\\activate"
else
    echo "       source venv/bin/activate"
fi
echo "  3. Start the app:"
echo "       streamlit run streamlit_app.py"
echo ""
echo "The app will open at http://localhost:8501"
