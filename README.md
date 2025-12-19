# AI Survivor Bridge

A Project Zomboid mod acting as a bridge between the game engine (Lua) and an external AI agent (Python).

## Architecture
See `docs/` for detailed architecture diagrams:
- [Bot Layering Architecture](docs/botLayeringArchitecture.txt)
- [Data Flow](docs/dataFlowArchitecture.txt)

## Developer Tools

### Automated Game Launch (`launch_pz.bat`)
Located in `dev_tools/`, this script automates the tedious process of launching the game and navigating the start screen.

**Usage:**
```batch
.\dev_tools\launch_pz.bat
```

**Features:**
- **Auto-Kill**: Terminates existing `ProjectZomboid64.exe` processes.
- **Auto-Click**: Launches `click_start_check.py` to monitor `console.txt`. Once the game is ready ("Removing undersized resolution mode" log detected), it automatically focuses the window and performs a mouse click to bypass the "Click to start" screen.
- **Log Cleanup**: Automatically removes old `console.txt` logs to ensure clean reads.

### Mouse Debugging
If you encounter input issues, use `dev_tools/debug_mouse_logger.py` to trace click coordinates and active window titles.
