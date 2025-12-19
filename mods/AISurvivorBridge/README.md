# AI Survivor Bridge (Project Zomboid Mod)

A Lua-based bridge for Project Zomboid (v42.13+) that exposes game state to external AI agents via JSON files (`state.json`) and accepts commands (`input.json`).

## 📋 Overview
This mod acts as the "eyes and ears" for an external AI agent. It:
1.  **Observes**: Serializes player stats, inventory, surroundings, and body damage into `state.json`.
2.  **Acts**: Reads `input.json` to execute actions like moving, interacting, or managing inventory.

## 🛠️ Prerequisites
- **Project Zomboid** (Build 42 beta / v42.13+)
- **Python 3.10+** (For automation scripts)
- **PowerShell** (Optional, for advanced scripts)

### Python Dependencies
No extra dependencies required for the Lua AutoLoader.

## 🚀 Installation
1.  **Clone/Copy** this folder into your Project Zomboid Mods directory:
    - `C:\Users\<YOU>\Zomboid\mods\AISurvivorBridge`
2.  **Enable the Mod**:
    - Launch Project Zomboid.
    - Go to **Mods**.
    - Toggle **AI Survivor Bridge** to ON.

## 🎮 Usage
### Manual Run
1.  Start a Single Player game (Sandbox/Survival).
2.  The mod initializes automatically on logic ticks.
3.  Check `C:\Users\<YOU>\Zomboid\Lua\state.json` for output.

### Automated Debugging (Recommended)
We have provided tools to restart the game quickly for development loops.

1.  **Launch Game (Debug Mode)**
    Run the batch file to kill any existing PZ process and launch a new one in debug mode:
    ```cmd
    dev_tools/launch_pz.bat
    ```
2.  **Auto Load Save**
    The mod includes a Lua script (`AutoLoader.lua`) that automatically loads the latest save on startup.
    - **To Disable**: Rename `media/lua/shared/AutoLoader.lua` to `AutoLoader.lua.disabled`.
    - **Configuration**: Edit `AutoLoader.lua` to adjust wait times or disable the "Click to Start" bypass.

## 📁 Project Structure
- `media/lua/client/` - Core Lua scripts.
    - `ObservationClient.lua` - State gathering logic.
    - `ActionClient.lua` - Action execution logic.
- `dev_tools/` - Windows automation scripts.

## ⚠️ Troubleshooting
- **Missing `state.json`**: Ensure you are loaded into a world (not just main menu).
- **Lua Errors**: Check `C:\Users\<YOU>\Zomboid\console.txt` for stack traces.
- **Moodles/Body Parts missing**: Ensure you are on v42.13+ as API names have changed.
