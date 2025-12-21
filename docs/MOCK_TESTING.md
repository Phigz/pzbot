# Mock Testing Guide

This guide describes how to run the full mock testing stack for PZBot. This allows you to test the bot's logic without launching the game.

## Prerequisites

Ensure you have set up your environment:
```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Running the Stack

You will need **3 separate terminal windows** to run the full stack.

### Terminal 1: The World (Mock Bridge)
This simulates the game engine, zombies, and environment.

```bash
./pzbot/tools/mock_bridge/run_mock.sh --scenario basic
```
*   **Args**:
    *   `--scenario basic`: Loads a player and a few zombies.
    *   `--scenario surrounded`: High danger scenario.

### Terminal 2: The Brain (Bot Runtime)
This runs the actual bot logic (pathfinding, decision making).

```bash
source venv/bin/activate
python3 -m pzbot.bot_runtime.main
```

### Terminal 3: The Eyes (Visualizer)
This opens a web view to show you what the bot "sees" and "thinks".

```bash
source venv/bin/activate
python3 -m pzbot.tools.visualize_grid
```

## Verification
1.  **Mock Bridge**: Should show `[MOCK] - Loaded scenario: basic`.
2.  **Bot Runtime**: Should log `Connected to state file...` and start processing ticks.
3.  **Visualizer**: Should handle a connection and display the grid map (usually at `http://localhost:8000` or similar, check console output).
