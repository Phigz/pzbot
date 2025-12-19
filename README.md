# PZBot: A Bot for Project Zomboid
**PZBot** is an experimental framework connecting Project Zomboid to external AI agents. It serves as a bidirectional bridge, allowing Python-based AI models to perceive the game state and control a character in real-time.

The project is designed to enable the development of autonomous agents capable of navigating, surviving, and thriving in the zombie apocalypse using modern AI techniques.

## 🏗️ Architecture Overview

The system consists of three primary components:

### 1. The Mod (`AISurvivorBridge`)
Located in `mods/AISurvivorBridge`, this Lua mod runs inside the game engine.
*   **Perception**: Scans the immediate environment (zombies, player stats, items) and writes structured JSON state to disk.
*   **Actuation**: Reads command files (`input.json`) and executes in-game actions (Walk, Run, Attack, Loot, etc.) using the internal game API.
*   **Automation**: Handles game lifecycle management, including auto-launching new sandbox games for training loops.

### 2. The Bot Runtime (`pzbot`)
Located in `pzbot`, this is the external Python brain.
*   **State Ingestion**: Monitors the game's output files for real-time state updates.
*   **World Modeling**: Builds a persistent 3D grid memory of walkability and tile data.
*   **Decision Engine**: Processes state data to make high-level survival decisions.
*   **Action Dispatch**: Converts high-level intents (e.g., "Flee from horde") into low-level atomic actions.

### 3. Developer Tools (`dev_tools`)
Utilities to streamline the development and testing loop.
*   **`launch_pz.bat`**: A single command to kill stale processes, configure launch options, and start the game in debug mode.
*   **`configure_launch.py`**: Manages launch configurations (New Game vs. Continue).
*   **`click_start_check.py`**: Automates the "Click to Start" interaction to ensure zero-interaction boot-up.
*   **`tools/visualize_grid.py`**: A live HTML map visualizer to inspect the bot's internal world model.

---

## � Usage

### 1. Launch the Game
Start Project Zomboid in debug mode with automated entry:
```powershell
# Start a fresh new game (auto-skips menus)
.\dev_tools\launch_pz.bat --new

# Or continue the last save
.\dev_tools\launch_pz.bat
```

### 2. Start the Bot Runtime
Launch the Python brain to begin perception and control. This must run alongside the game.
```powershell
python -m pzbot.main
```

### 3. Visualizer (Optional)
Open a real-time map view of what the bot "sees" and remembers.
```powershell
python pzbot/tools/visualize_grid.py
```

---

## 🗺️ Roadmap

### Phase 1: Foundation (Current)
- [x] **Bi-directional Communication**: Lua ↔ Python file-based bridge.
- [x] **Basic Actions**: Movement, looking, sitting, inventory interaction.
- [x] **State Perception**: Reading health, stats, and nearby zombie positions.
- [x] **Automation**: Fully automated new-game launch sequence.
- [x] **World Modeling**: Persistent grid memory and map visualization.

### Phase 2: Survival Competence
- [x] **Navigation**: A* Pathfinding integration (Python-side).
- [ ] **Combat Logic**: Basic kiting and melee engagement rules.
- [ ] **Looting Loop**: Identification of valuable items and inventory management.

### Phase 3: Advanced Intelligence
- [ ] **LLM Integration**: Connecting to Large Language Models for high-level goal planning (e.g., "Secure a base").
- [ ] **Visual Perception**: (Experimental) Using direct screen capture for vision-based inputs.
- [ ] **Memory**: Implementation of long-term memory for map knowledge and safehouse tracking.

---

## 📚 Documentation
Detailed documentation is available in the `docs/` directory:
*   [Unified Design & Architecture](docs/DESIGN.md)
*   [Input/State Schemas](docs/schemas/)
