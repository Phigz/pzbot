# World Model Design & Roadmap

## 1. Overview
The **World Model** is the bot's internal representation of the game state. It aggregates transient `vision` data into a persistent, queryable mental map. This layer is responsible for Object Permanence, Spatial Awareness, and Sensory Memory.

## 2. Core Components

### 2.1. Vision Ingestion
- **Source**: `state.json` (Lua Mod)
- **Logic**:
    - **Unified Radius**: 
        - All entities (Zombies, Loot) and Grid Tiles are scanned at **50 tiles** (or configured `VISION_RADIUS`).
    - **Cell-Centric**: (Proposed) Moving to cell-based updates for grid data.

### 2.2. Entity Manager (`EntityManager`)
- **Responsibility**: Tracks dynamic actors (Zombies, Players, Items).
- **Persistence**:
    - **ID Matching**: Updates existing entities if ID matches.
    - **Short-Term Memory (Ghosts)**: When an entity leaves vision, it is marked as `is_visible=False` (Ghost).
    - **Decay**: Ghosts are removed after a configurable TTL (`MEMORY_TTL`).
        - *Zombies*: 10s (Buffer for "Long" memory mechanic).
        - *Static*: 5m (Containers, Doors).

### 2.3. Spatial Grid (Planned)
- **Responsibility**: Persistent map of the physical world.
- **Data**:
    - **Walkability**: Walls, fences, open space.
    - **Floor Type**: Noise estimation (Carpet vs Wood).
    - **Discovery**: Fog-of-war tracking (Visited vs Unvisited).

## 3. Data Structures

### Vision Schema (JSON)
The raw input format from Lua.

```json
"vision": {
  "scan_radius": 15,
  "timestamp": 123456789,
  "entities": [
    {
      "id": "z_1054",
      "type": "Zombie",
      "x": 105.5, "y": 100.2, "z": 0,
      "meta": { "state": "chasing", "dist": 12.5 }
    }
  ],
  "debug_z": { "total": 50, "scan_log": "..." }
}
```

### Zombie State Enum
Maps raw PZ states to tactical categories:
- `IDLE`, `WANDER`: Passive/Low Threat.
- `CHASING`: **High Threat**.
- `ALERTED`: Caution.
- `ATTACKING`, `STAGGERING`, `CRAWLING`: Combat states.

## 4. Roadmap

### Phase 1: Foundation (Completed)
- [x] **Entity Tracking**: ID persistence.
- [x] **Short-Term Memory**: Ghosting and TTL Decay.
- [x] **Unified Vision**: Simpler single-radius scanning strategy.

### Phase 2: Spatial Awareness (Next)
- [ ] **Persistent Grid**: 2D Array/Map of all visited tiles.
- [ ] **A* Pathfinding**: Integrating Grid with `Navigator`.
- [ ] **Door State Memory**: Remember if a specific door ID was Open/Closed/Locked.

### Phase 3: Sensory Intelligence
- [ ] **Sound Events**: 
    - *Input*: "Gunshot at (X, Y)".
    - *Reaction*: Create transient "SoundSource" entity.
- [ ] **Scent/Pheromones**: Mark tiles as "Zombie Trail" if frequently traveled.
- [ ] **Heatmaps**: Decay-based density map of recent zombie sightings.

### Phase 4: Advanced Object Permanence
- [ ] **Loot Memory**: "I saw a Sledgehammer at Warehouse A 2 days ago."
- [ ] **Vehicle Memory**: Track drivable cars and their condition.

## 5. Common World Interface (Design)

To support higher-level reasoning (Interests, Opinions, Social), the World Model exposes a semantic query layer. This decouples decision-making from the raw state data.

### 5.1. The `WorldView` Protocol

A read-only interface provided to reasoning modules.

```python
class WorldView:
    @property
    def player(self) -> PlayerAgent: ...
    @property
    def environment(self) -> EnvironmentData: ...
    
    # Spatial Queries
    def find_nearest(self, type_filter: EntityType, radius: float = 50) -> List[Entity]: ...
    def get_objects_in_zone(self, zone_id: str) -> List[Entity]: ...
    
    # Semantic Queries
    def get_known_threats(self) -> List[Threat]: ...
    def get_interesting_items(self, interest_filter: Callable) -> List[Item]: ...
```

### 5.2. Event Bus (Planned)

Reasoning layers can subscribe to world events rather than polling every tick.

- `on_entity_sighted(entity)`: New zombie/player entered vision.
- `on_threat_level_change(new_level)`: Aggregate threat score changed.
- `on_zone_entered(zone_id)`: Player moved into a new room/building.

