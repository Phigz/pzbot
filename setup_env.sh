#!/bin/bash
# setup_env.sh
# Automates setting up the Python virtual environment and installing dependencies.

# Ensure we are in the project root
cd "$(dirname "$0")"

echo "[SETUP] Setting up PZBot environment..."

# 1. Create Virtual Environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[SETUP] Creating virtual environment 'venv'..."
    python3 -m venv venv
else
    echo "[SETUP] Virtual environment 'venv' already exists."
fi

# 2. Activate and Install
echo "[SETUP] Installing dependencies from requirements.txt..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "[SETUP] Done! You can now use the helper scripts:"
echo "  Run Mock Bridge: ./pzbot/tools/mock_bridge/run_mock.sh"
echo "  Run Bot Runtime: ./pzbot/tools/mock_bridge/run_mock_brain.sh"
