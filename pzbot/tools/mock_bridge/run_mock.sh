#!/bin/bash
# Helper script to run the mock bridge using the local virtual environment

# Ensure we are in the project root
# Script is in pzbot/tools/mock_bridge/run_mock.sh, so we go up 3 levels
cd "$(dirname "$0")/../../.."

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment 'venv' not found."
    echo "Please run: python3 -m venv venv && source venv/bin/activate && python3 -m pip install -r requirements.txt"
    exit 1
fi

# Run the mock bridge using the verify python executable
./venv/bin/python3 -m pzbot.tools.mock_bridge.main "$@"
