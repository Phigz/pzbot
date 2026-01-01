# PZBot Design

## 1. Overview
PZBot is a Python-based runtime designed to autonomously control a character in *Project Zomboid*. It interfaces with the game via the `AISurvivorBridge` Lua mod, exchanging data through JSON files on the local file system.

The goal is to create an agent capable of long-term survival through:
- **Perception**: Reading game state (vision, body, inventory).
- **Memory**: Building a persistent world model of the environment.
- **Planning**: Executing high-level goals (e.g., "Loot Warehouse", "Flee Horde").

---

## 2. System Architecture

The system consists of two main components operating in a loop:

### 2.1. The Lua Bridge (`AISurvivorBridge`)
- **Role**: The "Body" and "Senses".
- **Sensing**: Scans the environment and writes a snapshot to `state.json` every ~200ms.
- **Actuating**: Reads `input.json` for action batches (e.g., `move_to`, `look`) and executes them via the in-game API.

### 2.2. The Python Runtime (`pzbot`)
- **Role**: The "Brain".
- **Ingest**: Watches `state.json` for updates.
- **World Modeling**: Maintains a persistent internal representation of the world.
- **Navigation**: Plans paths using A* on the internal grid.
- **Control**: Manages the action queue and ensures smooth execution.

### 2.3. Data Flow Architecture

We model the system as a decoupled loop where data flows up from the game to the brain (Perception), and commands flow down from the brain to the game (Control).

#### 2.3.1. Incoming Data (Perception Pipeline)
The "Incoming" flow is responsible for turning raw, high-frequency game scans into a stable, queryable memory.

```
[Lua Mod] --(Scans Env)--> [state.json] --(File IO)--> [Python Ingest]
                                                          |
                                                      (Raw Dict)
                                                          v
                                                  [World Model]
                                                    /       \
                                            (Updates)       (Updates)
                                                v               v
                                         [Spatial Grid]   [Entity Tracker]
                                                \               /
                                            (Abstracted State)
                                                    v
                                             [Planning Layer]
```

#### 2.3.2. Outgoing Data (Action Pipeline)
The "Outgoing" flow translates high-level intents (e.g., "Loot House") into specific, frame-perfect game API calls.

```
[Planning Layer] --(Decision)--> [Action Controller]
                                        |
                                 (Atomic Commands)
                                        v
                                 [Command Queue]
                                        |
                                  (Serialization)
                                        v
                                   [input.json]
                                        |
                                    (File IO)
                                        v
                                    [Lua Mod] --(Game API)--> [Execute Action]
```

---

## 3. World Model
The **World Model** is the bot's internal representation of the game state. It aggregates transient `vision` data into a persistent, queryable mental map.

### 3.1. Vision Ingestion
- **Source**: `state.json` (Lua Mod)
- **Radius**: All entities (Zombies, Items) are scanned at 50 tiles.
- **Structure**:
    - `tiles`: List of walkable coordinates `(x, y, z)` currently in LoS.
    - `objects`: Dynamic entries (Zombies, Players) and static interactables (Doors, Windows, Containers).
    - `neighbors`: 3x3 immediate adjacency grid for rapid local avoidance and state checks.

### 3.2. Signal & Audio Ingestion
- **Source**: `signals` array in `state.json`.
- **Signals**: Radio and TV broadcasts (Message, Power, Channel).
- **Audio**: Hooks for `WorldSound` events are available but strictly "Last Heard" (Ambiguous Location) is currently disabled to avoid noise.
- **Purpose**: Allows the bot to locate powered electronics and "Home" locations (safehouses often have radios on).

### 3.3. Entity Manager
- **Responsibility**: Tracks dynamic actors (Zombies, Players, Items).
- **ID Matching**: Updates existing entities if ID matches.
- **Short-Term Memory (Ghosts)**: When an entity leaves vision, it is marked as `is_visible=False` (Ghost).
- **Decay**: Ghosts are removed after `MEMORY_TTL` (10s for Zombies, 5m for Static objects).

### 3.4. Container Memory
- **ContainerMemory**: Persists containers (Crates, Shelves) and their contents.
- **GlobalFloorMemory**: A singleton container (`Global_Floor`) that aggregates all items found on the floor (from Loot Window or World Scan).
    - **Purpose**: Provides a unified view of "Ground" items without spamming "Floor" containers for every tile.
    - **Persistence**: Items are tracked by ID; if an item disappears from vision (and isn't in 3x3 range), it decays after `MEMORY_TTL_GLOBAL`.

### 3.5. Spatial Grid (Implemented)
- **Responsibility**: Persistent map of the physical world.
- **Data Structure**: `SpatialGrid` class using a sparse dictionary of `GridTile` objects.
- **Features**:
    - **Walkability**: Derived from `w` flag in tile data.
    - **Discovery**: Tracks visited tiles and prevents "gaps" by filling in missing data with floor checks.
    - **Bounds**: Dynamically updates the bounding box of known territory.
    - **Semantic Layers**:
        - **Rooms**: Extracted from Lua `sq:getRoom()` (e.g., "Kitchen", "Garage").
        - **Layers**: Extracted from Sprite/Object classification:
            - `Tree`: Trees (canopy or trunk).
            - `Street`: Pavement/Roads.
            - `Wall`: Impassable building walls.
            - `FenceHigh`: Tall/Climbable fences.
            - `FenceLow`: Waist-high fences.
            - `Vegetation`: Grass/Plants.
            - `Floor`: Interior floors.
- **Visualization**: Inspectable via `tools/visualize_grid.py`, which renders the grid to an HTML Canvas with semantic color-coding (Rooms > Trees > Walls > Floors).

### 3.4. Navigation (Implemented)
- **Algorithm**: A* Pathfinding (`AStarPathfinder` in `nav.py`).
- **Heuristic**: Euclidean distance to target.
- **Cost Function**: Checks `SpatialGrid.is_walkable` (checks `w`, `n`, `e`, `s` collision flags).

---

## 4. API Reference

### 4.1. Input Schema (`input.json`)
The bot writes commands to `input.json`.

**Example:**
```json
{
  "sequence_number": 1,
  "clear_queue": false,
  "actions": [
    {
      "id": "uuid-string",
      "type": "move_to",
      "params": { "x": 100, "y": 100, "sprinting": false }
    }
  ]
}
```

**Common Actions:**
| Action | Params | Description |
|--------|--------|-------------|
| `move_to` | `x`, `y`, `z` | Move to coordinate. |
| `look_to` | `x`, `y` | Face a coordinate. |
| `wait` | `duration_ms` | Idle for time. |
| `sit` | (None) | Sit on ground. |

### 4.2. State Schema (`state.json`)
The mod writes perception data to `state.json`.

**Example:**
```json
{
  "timestamp": 1234567890,
  "tick": 1234,
  "player": {
    "status": "idle",
    "vitals": { "health": 100, "stamina": 1, "hunger": 0, "panic": 0 },
    "active_action_id": "uuid-string",
    "position": { "x": 10909.5, "y": 9995.2, "z": 0 },
    "state": { "aiming": false, "sneaking": false, "running": false, "is_sitting": false },
    "body": {
      "health": 100,
      "temperature": 37.0,
      "fatigue": 0.0,
      "hunger": 0.1,
      "thirst": 0.0,
      "panic": 0.0,
      "parts": {
        "Hand_L": { "health": 100, "bleeding": false, "bitten": false }
      }
    },
    "moodles": [
        { "name": "Panic", "value": 1, "sentiment": -1 },
        { "name": "Hungry", "value": 2, "sentiment": -1 }
    ],
    "inventory": [],
    "vision": {
      "scan_radius": 15,
      "tiles": [ { "x": 10909, "y": 9995, "z": 0, "room": "Kitchen" } ],
      "objects": [ { "id": "1845", "type": "Zombie", "x": 10912, "y": 9998, "meta": { "state": "CHASING" } } ],
      "neighbors": { "n": { "status": "walkable" }, "s": { "status": "blocked" } }
    }
  },
  "environment": {
    "nearby_containers": []
  },
  "events": []
}
```

---

## 5. Roadmap

### Phase 1: Foundation (DONE)
- [x] **Bi-directional Communication**: Lua ↔ Python bridge.
- [x] **State Perception**: Reading health, stats, nearby zombies.
- [x] **World Modeling**: Persistent grid memory and entity tracking.
- [x] **Visualization**: Live HTML map.
- [x] **Automation**: Auto-launch "New Game".
- [ ] **[STRETCH] Simulation Speed Resilience**: Graceful handling of game fast-forward (2x/3x/5x).

### Phase 2: World Modeling (WIP)
- [x] **Spacial Grid Memory**: Sparse persistent map of discovered tiles.
- [x] **Entity Tracking**: Dynamic tracking of entities (Zombies, Players, Items).
- [x] **Navigation**: A* pathfinding on the internal grid
- [x] **Semantic World Labels**: Buildings, rooms, interiors vs exteriors, etc.
- [ ] **Resource Awareness**: Known loot loctaions, seen container memory, etc.
- [ ] **Threat Modeling**: Zombie density, chase states, line-of-sight danger, etc.
- [ ] **Event Awareness**: Gunshots, explosions, player chat, etc.
- [ ] **Brain State Serialization**: Save/Load mechanism for persistent world knowledge across sessions.
- [ ] **Social Awareness**: Memory of players, behavior, etc.

#### Implementation Notes
- Consumes the state
- Emits the world model

This phase answers:
> "What exists in the world, where is it, and how reliable is my knowledge?"

### Phase 3: Reactive Control (TODO)
- [ ] **Threat Response**: Depends on if threat is zombie or player.
- [ ] **Critical Needs**: Bleeding, starving, etc.
- [ ] **Local Navigation**: Avoid blocked or dangerous tiles, re-pathing.
- [ ] **Interrupt Architecture**: Subsumption-style logic where raw safety (fleeing) suppresses tactical plans.
- [ ] **Social Response**: How to interact with other players.

#### Implementation Notes
- Consumes the world model
- Emits short-lived action sequences
- Can override higher-level plans when necessary

This phase answers:
> "What must I do right now to avoid dying?"

### Phase 4: Tactical Planning (TODO)
- [ ] **Goal Decomposition**: "Loot this house", "Clear nearby zombies", etc.
- [ ] **Multi-step Planning**: Navigate -> interact -> wait -> observe -> react.
- [ ] **Inventory & Resource Constraints**: Capacity-aware looting, tool requirements, etc.
- [ ] **Risk Evaluation**: Zombie density vs reward, escape path availability, etc.
- [ ] **Objective Failure Handling**: Re-planning and learning from failed attempts (e.g. locked doors).
- [ ] **Social Planning**: How to interact with other players (e.g. trading, short-term cooperation, avoidance, etc).

#### Implementation Notes
- Likely hybrid:
 - Deterministic planners (GOAP-style)
 - Optional lightweight model assistance
- Outputs plans that are:
 - Interruptible
 - Verifiable
 - Recoverable on failure

This phase answers: 
> "How do I achieve my current objective safely and efficiently?"

### Phase 5: Strategic and Long-Term Planning (TODO)
- [ ] **Long-Term Goal Formation**: Base building, skill training, etc.
- [ ] **Persistent Memory**: Important locations, past encounters, learned risks, etc.
- [ ] **Preference Modeling**: Risk tolerance, playstyle bias, personal "values", etc.
- [ ] **Personality & Archetypes**: Defining traits (Brave, Cowardly, Looter) that guide LLM intent.
- [ ] **Context Summarization**: Translating raw World Model data into semantic natural language for LLM reasoning.
- [ ] **Relationship Management**: High-level social strategy and group alignment.

#### Implementation Notes
- LLM-backed orchestration layer
- Consumes:
 - Summarized world model
 - Tactical outcomes
 - Historical memory
- Produces:
 - High-level intents
 - Constraints and priorities

This phase answers:
> "Who am I, and what kind of survivor am I trying to be?"

---

## 6. Character Design System
We use a structured system to define bot personalities and capabilities, ensuring consistency between roleplay elements (LLM context) and in-game mechanics (skills, traits).

### 6.1. Design Template (`docs/character_design_sheet.md`)
A markdown template used to brainstorm and define:
- **Core Identity**: Name, age, origin, and pre-apocalypse occupation.
- **Game Mechanics**: Profession, traits (positive/negative), and starting skills.
- **Dynamic Physicality**: Appearance, weight tendencies, and clothing strategies that evolve during play.
- **Behavioral Logic**: Explicit preferences for combat (Fight/Flight), looting, and socialization.

### 6.2. JSON Schema (`docs/schemas/character_schema.json`)
A formal JSON Schema definition that validates character files. This integration allows us to:
- Programmatically generate unique bot backstories.
- Validate that traits and professions match game data.
- Load personality parameters directly into the bot's logic engine at runtime.

---

## 6. Debugger & Observability
The bot features a real-time visual debugger (`pzbot/tools/debug_bot.py`) that acts as the primary observability tool.

### 6.1. Architecture
The debugger is split into a minimal Python HTTP server and a modern Web Client:
- **Server** (`pzbot/tools/debug_bot.py`): Serves static files and exposes `state.json` via `/data` endpoint.
- **Client** (`pzbot/tools/web/`):
  - `index.html`: UI scaffolding.
  - `app.js`: Logic for polling `/data`, rendering the Canvas map, and managing DOM updates.
  - `style.css`: Dark-themed visual styling.

### 6.2. Visualization Layers
1.  **Live State**: Renders raw data from `Sensor.lua` (Green=Player, Red=Zombie, Blue=Vehicles).
2.  **Memory Model**: Renders the bot's internal cache (`MemorySystem`). Visually distinct (faded colors) to verify persistence logic.
3.  **Bio & Vitals**: Real-time bars for Health, Hunger, Thirst, Panic, Boredom, and Sanity.
4.  **Semantic Map**: Displays tiles with color codes for Wall, Floor, Window, etc.
