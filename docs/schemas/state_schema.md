# PZBot World Model Schema (`state.json`)

This document describes the structure of the JSON payload sent from the Lua Mod (`AISurvivorBridge`) to the Python Runtime (`pzbot`).

## Root Object (`GameState`)
| Field | Type | Description |
|---|---|---|
| `timestamp` | `float` | Server time in seconds. |
| `tick` | `float` | Game world tick count. |
| `player` | `Player` | The bot's character state. |
| `environment` | `Environment` | (Optional) Global environment data. |

---

## 1. Player
| Field | Type | Description |
|---|---|---|
| `guid` | `string` | Unique ID of the character. |
| `player_num` | `int` | Local player index (usually 0). |
| `position` | `Position` | `{x, y, z}` coordinates. |
| `body` | `PlayerBody` | Health, Stamina, Hunger, Thirst, etc. |
| `flags` | `PlayerStateFlags` | Booleans for states (aiming, running, etc). |
| `stats` | `dict` | Raw stats dump (XP, Perks). |
| `vision` | `Vision` | **CRITICAL**: The bot's sensory input (Live Entities). |
| `moodles` | `List[Moodle]` | Active positive/negative effects. |
| `inventory` | `List[Item]` | Items in the main inventory. |
| `action_state`| `ActionState` | Status of the current action being executed. |

### 1.1 ActionState
Tracks the progress of the current action (if any).
| Field | Type | Description |
|---|---|---|
| `status` | `string` | "idle", "active", "complete", "failed". |
| `current_action_id` | `string` | UUID of the executing action. |
| `current_action_type`| `string` | Debug text (e.g. "WalkTo"). |
| `queue_busy` | `bool` | True if internal action queue is processing. |

### 1.2 Body (`PlayerBody`)
| Field | Type | Description |
|---|---|---|
| `health` | `float` | 0.0 - 1.0 (Dead - Full) |
| `stamina` | `float` | 0.0 - 1.0 (Exhausted - Rested) |
| `hunger` | `float` | 0.0 - 1.0 (Full - Starving) |
| `thirst` | `float` | 0.0 - 1.0 (Quenched - Dehydrated) |
| `fatigue` | `float` | 0.0 - 1.0 (Awake - Collapsing) |
| `panic` | `float` | 0.0 - 1.0 (Calm - Terrified) |
| `temperature` | `float` | Body temp (approx 37.0 normal). |
| `is_infected` | `bool` | Zombie infection status. |
| `is_bitten` | `bool` | Injury status. |
| `parts` | `Dict[str, Part]` | Detail on specific limbs (e.g. "Hand_L"). |

---

## 1.2 Body Part (`Part`)
| Field | Type | Description |
|---|---|---|
| `health` | `float` | 0-100% |
| `bleeding` | `bool` | Is actively bleeding. |
| `bitten` | `bool` | Is bitten (high infection risk). |
| `scratched` | `bool` | Is scratched. |
| `fracture` | `bool` | Is broken. |
| `bandaged` | `bool` | Is currently treated. |

---

## 2. Environment (`Environment`)
Global weather and lighting context.

| Field | Type | Description |
|---|---|---|
| `time_of_day` | `float` | 0.0 - 24.0 (Hours). |
| `weather` | `string` | Synthesized summary: "Clear", "Raining", "Storm", "Foggy". |
| `temperature` | `float` | Air temperature around character (Celsius). |
| `wind_speed` | `float` | 0.0 - 1.0 (Calm - Hurricane). |
| `light_level` | `float` | 0.0 - 1.0 (Pitch Black - Bright Daylight). |
| `rain` | `float` | 0.0 - 1.0 intensity. |
| `fog` | `float` | 0.0 - 1.0 intensity. |
| `clouds` | `float` | 0.0 - 1.0 intensity. |

---

## 2. Vision (`Vision`)
This contains all entities the bot can currently "see".

| Field | Type | Description |
|---|---|---|
| `scan_radius` | `int` | Radius of the scan in tiles. |
| `tiles` | `List[Tile]` | Grid info (walls, floors) around the bot. |
| `objects` | `List[WorldObject]` | Dynamic entities (Zombies, Players, Animals). |
| `vehicles` | `List[Vehicle]` | Vehicles in range. |
| `nearby_containers` | `List[Container]` | Lootable containers within reach/vision. |
| `world_items` | `List[WorldItem]` | Items on the floor. |
| `signals` | `List[Signal]` | Active TV/Radio broadcasts. |
| `sounds` | `List[Sound]` | Heard audio events. |

### 2.1 WorldObject (Entity)
Used for Zombies, Players, Animals.

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Unique Entity ID. |
| `type` | `string` | "Zombie", "Player", "Animal". |
| `x`, `y`, `z` | `float` | Position. |
| `meta` | `dict` | Entity-specific data. |

**Meta Fields (Zombie/Player):**
*   `state`: Current animation state (e.g., "idle", "attack").
*   `weapon`: Name of equipped weapon.
*   `worn`: List of visible clothing.

**Meta Fields (Animal):**
*   `species`: "Cow", "Chicken", etc.
*   `breed`: Sub-type.
*   `age`: Age value.
*   `health`: Health value.
*   `isMale`, `isFemale`: Gender flags.
*   `milking`: Boolean (is milking in progress?).
*   `canBePet`: Boolean.

### 2.2 Interactibles (World Objects)
New classification for functional objects found via grid scan.

| Type | Meta Fields | Description |
|---|---|---|
| `Stove` / `Microwave` | `activated`, `temp` | Cooking appliances. |
| `Generator` | `activated`, `fuel`, `cond` | Power source. |
| `TV` / `Radio` | `activated`, `channel`, `vol` | Entertainment/News. |
| `Light` | `activated`, `room` | Light switches and lamps. |
| `Washer` / `Dryer` | `activated` | Laundry machines. |

---

## 3. Containers & Items

### 3.1 Container
| Field | Type | Description |
|---|---|---|
| `type` | `string` | "Container" |
| `object_type` | `string` | Sprite/Script name (e.g. "Base.Crate"). |
| `x`, `y`, `z` | `int` | Position. |
| `items` | `List[Item]` | Contents of the container. |

### 3.2 Item
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Unique Item ID. |
| `type` | `string` | Full script name (e.g. "Base.Axe"). |
| `name` | `string` | Display name. |
| `category` | `string` | "Weapon", "Food", "Clothing", etc. |
| `count` | `int` | Stack size. |
| `cond` | `float` | Condition (0.0 - 1.0). Optional. |

---

## 4. Signals (`Signal`)
| Field | Type | Description |
|---|---|---|
| `type` | `string` | "Radio" or "TV". |
| `name` | `string` | Name of the device. |
| `channel` | `int` | Tuned frequency/channel. |
| `msg` | `string` | The text being broadcasted. |
| `x`, `y`, `z` | `int` | Source location. |

---

## 5. Notes on Data Types
*   **Lists vs Dicts**: Lua tables are ambiguous. An empty table `{}` becomes `{}` (dict) in JSON, but sometimes we expect `[]` (list).
*   **Pydantic Handling**: The Python runtime's `state.py` includes validators to handle this ambiguity, converting empty dicts to empty lists where appropriate.
*   **Missing Fields**: If a field is missing in Lua, it is usually omitted in JSON. Python models use default values.
