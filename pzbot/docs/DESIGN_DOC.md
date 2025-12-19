# PZBot Design Document & Project Plan

## 1. Overview
PZBot is a Python-based runtime designed to autonomously control a character in *Project Zomboid*. It interfaces with the game via the `AISurvivorBridge` Lua mod, exchanging data through JSON files on the local file system.

## 2. Architecture

The system consists of two main components operating in a loop:

### 2.1. The Lua Bridge (`AISurvivorBridge`)
- **Role**: The "Body" and "Senses" of the bot.
- **Responsibility**:
    - **Sensing**: Periodically scans the environment (tiles, objects, zombies, player status) and writes a snapshot to `state.json`.
    - **Actuating**: Reads `input.json` for a batch of actions (e.g., `move_to`, `look`, `attack`) and executes them using the in-game API.
    - **Feedback**: Reports the status of action execution (idle, executing, busy) in `state.json`.

### 2.2. The Python Runtime (`pzbot`)
- **Role**: The "Brain" of the bot.
- **Responsibility**:
    - **Ingest**: Watches `state.json` for updates and parses it into strict types (Pydantic models).
    - **World Modeling**: Maintains a persistent internal representation of the world.
        - **Aggregated Grid**: Merges partial `vision` data into a global map of visited tiles (walls, walkable areas).
        - **Entity Tracking**: Tracks dynamic objects (zombies, loot) across frames by ID and estimates positions when out of sight.
    - **Navigation**: Uses the persistent map to plan paths (A*) through known safe areas to unexplored frontiers.
    - **Planning**: Determines high-level goals (e.g., "Find Food") and decomposes them into executable actions.
    - **Control**: Manages the action queue and ensures smooth execution flow.
    - **IO**: Serializes actions and writes them to `input.json`.

### 2.3. Reasoning Layer (New)
- **Role**: The "Consciousness" / Higher-level cognition.
- **Responsibility**:
    - Consumes data via the `Common World Interface` (WorldView).
    - Formulates **Interests** (What do I want?), **Opinions** (Do I like this?), and **Relationships** (Friend/Foe).
    - Feeds high-level directives to the Planning layer.

## 3. Directory Structure (`pzbot/`)

- `bot_runtime/`
    - `main.py`: Entry point. Initialized components and starts the loop.
    - `ingest/`: Handles file watching and JSON parsing (Pydantic models).
    - `world/`: `WorldModel` implementation (State storage, Grid persistence, Entity mapping).
    - `planning/`: (Future) Decision making modules.
    - `control/`: `ActionQueue`, `BotController`, and `Navigator` (A* pathfinding).
    - `io/`: `InputWriter` and `InputSequencer`.

## 4. Current Status

### Lua Side
- **API**: Defined in `docs/API_DOCUMENTATION.md`.
- **Capabilities**:
    - Movement (`move_to`, `pathfind`)
    - Interaction (`look_to`, `look`)
    - Stance (`wait`, `sit`, `toggle_crouch`)
- **State Reporting**: Robust `state.json` schema including Vision, Inventory, Body status, and Action State.

### Python Side
- **Structure**: Core directory structure and entry points are established.
- **Runtime**:
    - `StateWatcher` is implemented.
    - `BotController` exists but is currently a pass-through (no intelligence yet).
    - `WorldModel` is a simple state wrapper.
    - `InputWriter` is ready to write.

## 5. Roadmap

### Phase 1: Foundation (Current)
- [x] Establish JSON Bridge (schemas).
- [x] Build Lua Action Executor.
- [x] Build Python State Ingestion.
- [x] **Verify End-to-End Loop**: Ensure the Python bot can read state, decide to wait/move, and the Lua mod executes it successfully.
- [x] **Test Framework**: Implemented `TestSequencer` for manual verification.

### Phase 2: World Model & Navigation (Current)
- [x] **Entity Tracking**: Track dynamic objects (ID persistence).
- [x] **Short-Term Memory**: "Ghost" entities that persist after leaving vision (Time-To-Live decay).
- [x] **Split Vision**: Optimized scanning (50 tiles for Threats, 15 for Loot).
- [ ] **Persistent Map**: Aggregated grid of visited tiles (Walls/Floor).
- [ ] **Navigation**: Implement A* pathfinding (`Navigator`).

### Phase 3: Complex Actions
- [ ] **Inventory Management**: Equip weapons, transfer items.
- [ ] **Combat**: Logic for engaging or fleeing from zombies.
- [ ] **Looting**: Systematic exploration of containers.

### Phase 4: Long-Term Autonomy
- [ ] **Goal-Oriented Action Planning (GOAP)**: Dynamic goal selection.
- [ ] **Survival Strategies**: Base building, farming, etc.

## 6. World Model (Detailed Design)

> [!NOTE]
> The detailed design, schema, and roadmap for the World Model layer have been moved to:
> **[WORLD_MODEL.md](./WORLD_MODEL.md)**

Please refer to that document for:
- Vision Ingestion & Schema
- Entity Manager Logic (Ghosts, Decay)
- Spatial Grid & Pathfinding Plans
- Sensory Memory (Sound, Scent) & Brainstorming

## 7. Resources
- **API Documentation**: `pzbot/docs/API_DOCUMENTATION.md`
- **World Model Design**: `pzbot/docs/WORLD_MODEL.md`
