# AISurvivorBridge API Documentation

This document describes the schema for the input and output JSON files used to interface with the AISurvivorBridge mod for Project Zomboid.

## 1. Input Schema (`input.json`)

The `input.json` file is used to send commands to the bot. It contains a batch of actions that the bot will execute sequentially.

### Structure

```json
{
  "sequence_number": 1,          // Monotonically increasing sequence number for this batch
  "id": "batch_unique_id",       // Unique identifier for this batch (optional/legacy)
  "timestamp": 123456789,        // Timestamp of creation
  "clear_queue": false,          // If true, clears any existing actions in the bot's queue before adding these
  "actions": [                   // List of action objects
    {
      "id": "uuid-string",       // Unique ID for this specific action instance
      "type": "action_type_name",
      "params": {
        "param1": "value"
      }
    }
  ]
}
```

### Action Reference

The following actions are available. Note that parameters marked as optional usually have sensible defaults.

#### Movement

| Type | Params | Description |
|------|--------|-------------|
| `move_to` | `x` (number)<br>`y` (number)<br>`z` (number, optional, default=0)<br>`sprinting` (bool, optional)<br>`running` (bool, optional) | Moves the player to the specified coordinate. Supports walking, running, or sprinting. |
| `pathfind` | `x` (number)<br>`y` (number)<br>`z` (number, optional, default=0) | Uses the game's pathfinding system to walk to a location. Similar to `move_to` but strictly uses vanilla walk action. |

**Aliases**: `moveto`, `walk` -> `move_to`

#### Vision & Interaction

| Type | Params | Description |
|------|--------|-------------|
| `look_to` | `x` (number), `y` (number) <br>**OR**<br>`target`: object `{x: number, y: number}` | Makes the player face a specific coordinate. |
| `look` | `target`: object `{x: number, y: number}` | **Warning**: `look` requires the nested `target` object style, while `look_to` accepts flat x,y. |

**Aliases**: `lookto` -> `look_to`

#### Stance & Idling

| Type | Params | Description |
|------|--------|-------------|
| `wait` | `duration_ms` (number) | Makes the bot wait/idle for the specified duration in milliseconds. |
| `sit` | *(None)* | Forces the bot to sit on the ground. |
| `toggle_crouch`| `active` (boolean) | Sets the sneaking/crouching state. `true` to crouch, `false` to stand. |

**Aliases**: `togglecrouch` -> `toggle_crouch`

---

## 2. State Schema (`state.json`)

The `state.json` file is written by the mod periodically (default ~200ms) and represents the bot's current perception of the world.

### Structure

```json
{
  "timestamp": 1234567890,       // Unix timestamp (ms)
  "tick": 12.34,                 // World Age (Hours)
  "player": {
    "status": "idle",            // General status (legacy, see action_state for detailed status)
    "position": { "x": 0, "y": 0, "z": 0 },
    "rotation": 0.0,             // Direction angle (0-360)
    "state": {
      "aiming": false,
      "sneaking": false,
      "running": false,
      "sprinting": false,
      "in_vehicle": false,
      "is_sitting": false
    },
    "body": {
      "health": 100,             // Overall health (0-100)
      "temperature": 37.0,
      "parts": {                 // Dictionary of body parts
        "Hand_L": {
          "health": 100,
          "bandaged": false,
          "bleeding": false,
          "bitten": false,
          "scratched": false,
          "deep_wound": false
        }
        // ... (Hand_R, Head, Neck, Torso_Upper, etc.)
      }
    },
    "moodles": {                 // Active moodles only
      "Thirst": 1,
      "Hungry": 2
    },
    "inventory": {
      "held": {
        "primary": { "id": 123, "name": "Axe", "type": "Base.Axe", ... } | null,
        "secondary": { ... } | null
      },
      "worn": [ ...List of Item Objects... ],
      "main": [ ...List of Item Objects... ]
    },

    "vision": {
      "scan_radius": 10,
      "timestamp": 1234567890,
      "tiles": [                 // List of currently visible, walkable tiles
        { "x": 100, "y": 100, "z": 0 }
      ],
      "objects": [               // Detected entities (Zombies, Players, Doors, Windows)
        {
          "id": "100_100_0",
          "type": "Zombie",
          "x": 100, "y": 100, "z": 0,
          "meta": { "dist": 5.4 }
        }
      ],
      "neighbors": {             // Immediate 3x3 grid status
        "n": { "x": 100, "y": 99, "status": "walkable", "objects": [] },
        "s": { "x": 100, "y": 101, "status": "blocked", "objects": [...] },
        "e": ...
      },
      "debug_z": {                // Debug Use Only
          "total": 50,
          "scan_log": "..."
      }
    },
    "action_state": {
      "status": "idle" | "executing",
      "sequence_number": 1,
      "queue_busy": false,
      "current_action_id": "uuid-string" | null,
      "current_action_type": "string" | null
    }
  }
}
```

### Action State Details

The `action_state` object provides feedback on the bot's current execution status within the command queue.

*   `status`: High-level status ("idle" or "executing").
*   `sequence_number`: The `sequence_number` of the batch currently being processed/tracked.
*   `queue_busy`: `true` if the bot is actively running a timed action (like walking or reading).
*   `current_action_id`: The UUID of the action currently being executed.
*   `current_action_type`: The type of the action currently running (e.g., "wait", "move_to").

### Vision Objects

The `vision.objects` list contains entities spotted within the `scan_radius` and line-of-sight.

| Type | Meta Data |
|------|-----------|
| `Zombie` | `dist` (distance), `state` (Enum: IDLE, WANDER, CHASING, ALERTED, ATTACKING, CRAWLING, STAGGERING) |
| `Player` | *(None)* |
| `Door` | `open` (boolean) |
| `Window` | `open` (boolean) |
| `Container` | `cat` (container type) |

### Item Schema

Items in `inventory.held`, `inventory.worn`, and `inventory.main` follow this structure:

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique in-game ID for the item instance. |
| `name` | string | Display name (e.g., "Fire Axe"). |
| `type` | string | Full item type (e.g., "Base.Axe"). |
| `cat` | string | Category (e.g., "Weapon", "Food"). |
| `weight` | number | Weight of the item. |
| `cond` | number | Condition (0.0 - 1.0 or similar floating point). |

---

## 3. Configuration (`config.yaml`)

The bot runtime is configurable via `pzbot/config/config.yaml`.

| Key | Default | Description |
|-----|---------|-------------|
| `MEMORY_TTL_ZOMBIE` | `10000` (10s) | Time to remember "Ghost" zombies after line-of-sight is lost. |
| `MEMORY_TTL_STATIC` | `300000` (5m) | Time to remember static objects (containers, doors). |
| `VISION_RADIUS_ZOMBIE` | `50` | Maximum radius (tiles) to scan for zombies. Matches Lua script logic. |
| `VISION_RADIUS_GRID` | `15` | Radius to scan for static tiles/objects. Lower value saves performance. |
| `LOG_LEVEL` | `INFO` | Console logging verbosity (DEBUG, INFO, WARNING). |
