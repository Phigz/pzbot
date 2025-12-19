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

### 2.3. Data Flow Diagram
```
- Lua[PZ Mod (Lua)] -->|Writes state.json| Ingest[Observation Ingest]
- Ingest -->|Normalizes| Model[World Model]
- Model -->|Belief State| Plan[Planner/Controller]
- Plan -->|Generates Actions| Queue[Action Queue]
- Queue -->|Writes input.json| Lua
```

---

## 3. World Model
The **World Model** is the bot's internal representation of the game state. It aggregates transient `vision` data into a persistent, queryable mental map.

### 3.1. Vision Ingestion
- **Source**: `state.json` (Lua Mod)
- **Radius**: All entities (Zombies, Items) are scanned at 50 tiles.

### 3.2. Entity Manager
- **Responsibility**: Tracks dynamic actors (Zombies, Players, Items).
- **ID Matching**: Updates existing entities if ID matches.
- **Short-Term Memory (Ghosts)**: When an entity leaves vision, it is marked as `is_visible=False` (Ghost).
- **Decay**: Ghosts are removed after `MEMORY_TTL` (10s for Zombies, 5m for Static objects).

### 3.3. Spatial Grid (Implemented)
- **Responsibility**: Persistent map of the physical world.
- **Data Structure**: `SpatialGrid` class using a sparse dictionary of `GridTile` objects.
- **Features**:
    - **Walkability**: Walls, fences, and open space derived from nav-grid data.
    - **Discovery**: Tracks visited tiles.
    - **Bounds**: Dynamically updates the bounding box of known territory.
- **Visualization**: Inspectable via `tools/visualize_grid.py`, which renders the grid to an HTML Canvas.

### 3.4. Navigation (Implemented)
- **Algorithm**: A* Pathfinding (`AStarPathfinder` in `nav.py`).
- **Heuristic**: Euclidean distance to target.
- **Cost Function**: Checks `SpatialGrid.is_walkable` (checks `w`, `n`, `e`, `s` collision flags).

---

## 4. API Reference

### 4.1. Input Schema (`input.json`)
The bot writes commands to `input.json`.

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

```json
{
  "timestamp": 1234567890,
  "player": {
    "position": { "x": 0, "y": 0, "z": 0 },
    "body": { "health": 100 },
    "vision": {
      "tiles": [{ "x": 100, "y": 100, "z": 0 }],
      "objects": [{ "type": "Zombie", "x": 100, "y": 100, "meta": { "state": "chasing" } }]
    }
  }
}
```

---

## 5. Roadmap

### Phase 1: Foundation (Completed)
- [x] **Bi-directional Communication**: Lua ↔ Python bridge.
- [x] **State Perception**: Reading health, stats, nearby zombies.
- [x] **World Modeling**: Persistent grid memory and entity tracking.
- [x] **Visualization**: Live HTML map.
- [x] **Automation**: Auto-launch "New Game".

### Phase 2: Survival Competence (Current)
- [x] **Navigation**: A* Pathfinding (Backend implemented).
- [ ] **Combat Logic**: Kiting and melee engagement rules.
- [ ] **Looting Loop**: Identification of valuable items and inventory management.
- [ ] **Exploration**: Frontier-based exploration logic.

### Phase 3: Advanced Intelligence
- [ ] **LLM Integration**: Connecting to LLMs for goal planning.
- [ ] **Long-Term Memory**: "I saw a Sledgehammer at Warehouse A".
- [ ] **Sound/Scent**: Reacting to gunshot events or trails.
