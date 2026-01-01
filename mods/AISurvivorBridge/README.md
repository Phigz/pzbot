# AI Survivor Bridge (Project Zomboid Mod)

A Lua-based bridge for Project Zomboid (v42.13+) that exposes game state to external AI agents via JSON files (`state.json`) and accepts commands (`input.json`).

## 📋 Overview
This mod acts as the "eyes and ears" for an external AI agent. It:
1.  **Observes**: Serializes player stats, inventory, surroundings, and body damage into `state.json`.
2.  **Acts**: Reads `input.json` to execute actions like moving, interacting, or managing inventory.

## 📁 Project Structure
- `media/lua/client/` - Core Lua scripts.
    - `ObservationClient.lua` - State gathering logic.
    - `ActionClient.lua` - Action execution logic.
- `dev_tools/` - Automation scripts.

## ⚠️ Troubleshooting
- **!!Panic!!**