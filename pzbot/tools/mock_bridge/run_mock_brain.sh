#!/bin/bash
# Helper script to run the bot runtime configured for the mock environment

# Ensure we are in the project root
# Script is in pzbot/tools/mock_bridge/run_mock_brain.sh, so we go up 3 levels
cd "$(dirname "$0")/../../.."

# Export Env Vars to override config defaults for Mock Mode
# Mock bridge writes to project root (./state.json)
# Config BASE_DIR is pzbot/
# So relative path is ../state.json
export PZBOT_STATE_FILE_PATH="../state.json"
export PZBOT_INPUT_FILE_PATH="../input.json"

echo "[RUNTIME] Starting Bot Brain in MOCK MODE..."
echo "[RUNTIME] Watching state at: $(pwd)/state.json"

# Check venv
if [ -d "venv" ]; then
    ./venv/bin/python3 -m pzbot.bot_runtime.main
else
    # Fallback to system python if expected venv is missing
    python3 -m pzbot.bot_runtime.main
fi
