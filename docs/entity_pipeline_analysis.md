# Entity Pipeline Analysis

## 1. Current State (The "Zombie Pipeline")
Currently, the system is hardcoded to prioritize Zombies, though the schema is somewhat generic.

### A. Lua (`Sensor.lua`)
- **Function**: `getZombieInfo(zombie, player)`
- **Scan Loop**: Iterates `getCell():getZombieList()`.
- **Output**:
  ```lua
  {
    id = "123",
    type = "Zombie",
    x = 100, y = 100, z = 0,
    meta = { state = "CHASING", dist = 5.4 }
  }
  ```
- **Limitation**: Only scans `IsoZombie`. Ignores `IsoPlayer` (other than self) and `IsoAnimal`.

### B. State Schema (`state.py`)
- **Model**: `Vision.objects` is `List[WorldObject]`.
- **WorldObject**:
  ```python
  class WorldObject(LogExtraFieldsBase):
      id: str
      type: str
      x: int; y: int; z: int
      meta: Dict[str, Any]
  ```
- **Status**: **Ready**. The schema is generic enough to accept `type="Player"` or `type="Chicken"`.

### C. Memory System (`memory_system.py`)
- **Ingest**: Maps `vision.objects` -> `self.entities` (Dict of `EntityMemory`).
- **EntityMemory**:
  - **TTL**: Hardcoded to `settings.MEMORY_TTL_ZOMBIE`.
  - **Decay**: Linear confidence drop.
- **Limitation**: Treating a friendly Player or a Cow as a Zombie for decay/memory purposes might be wrong (e.g., Players might need longer memory, Animals might need shorter).

## 2. Generalization Plan (Phase B-D)

### Phase B: Investigation (Lua APIs)
Need to identify correct Project Zomboid Java APIs:
- **Players**: `getCell():getRemoteSurvivorList()`? `IsoPlayer`?
- **Animals** (B42): `getCell():getAnimals()`? `IsoAnimal`? 
- **Properties**:
  - `Player`: formatting (username), `isPvp`, `weapon`.
  - `Animal`: `getAnimalType()`.

### Phase C: Design
1.  **Lua**: Create `getActorInfo(obj)` helper replacing `getZombieInfo`.
    - Detect class (`IsoZombie`, `IsoPlayer`, `IsoAnimal`).
    - Extract common props (pos, id) + specific props (username, state).
2.  **Python**: Update `EntityMemory.get_ttl()` to switch based on `self.data.type`.
    - `Zombie`: 10s
    - `Player`: 30s (Harder to lose track of?)
    - `Animal`: 20s

### Phase D: Execution
1.  Refactor `Sensor.lua` to scan all `IsoGameCharacter` objects.
2.  Update `config.py` with `MEMORY_TTL_PLAYER`, `MEMORY_TTL_ANIMAL`.
3.  Visualize in `debug_bot.py`.
