# Changelog

All notable changes to the PZBot project will be documented in this file.

## [0.2.0] - 2025-12-30

### Semantic World Modeling & Entity Intelligence
- **Entity Schema & Persistence**:
    - **Unified World Model (`docs/schemas/world_entities.md`)**: Formalized schema separation between "Live" (Observation) and "Memory" (Belief) data.
    - **Persistence Debugging**: Fixed a major bug where flattened entity memory properties were not being correctly read by the visualizer.
    - **Codified Models**: Added explicit `AnimalProperties`, `ZombieProperties`, and `PlayerProperties` schemas to Python runtime (`types.py`).

- **Deep Entity Introspection**:
    - **Animal Data**: Expanded `Sensor.lua` to extract highly detailed Animal metadata:
        - `Breed`, `Species`, `Age`, `Health`, `Gender`.
        - `Hunger`, `Thirst`, `Size`.
        - Interaction Flags: `isPetable`, `canBeAttached`, `isMilking`.
    - **Backpack Scanning**: Added logic to detect worn containers (Bags/Packs) on Zombies/Players.
    - **Visual Debugger**: Live and Memory tabs now display full metadata (including interaction flags and health %) consistently.

## [0.1.0] - 2025-12-19

### Semantic World Modeling
- **Perception (`Sensor.lua`)**:
    - Implemented logic to extract "Room" names from tiles (`sq:getRoom()`).
    - Implemented Semantic Layer classification (`getSemanticLabel`):
        - Distinguishes: `Tree`, `Street`, `Wall`, `FenceHigh`, `FenceLow`, `Vegetation`, `Floor`.
    - Fixed specific bug where "Street" sprites were misclassified as "Tree".
    - Fixed "Gap" issue where blocked tiles (Walls/Trees) were excluded from updates; now all visible tiles are reported with a `w` (walkable) boolean flag.
    - Increased Scan Frequency to 10hz (100ms) for smoother updates.

- **World Model (`pzbot`)**:
    - Updated `Tile` schema to include `room`, `layer`, and `w` fields.
    - Updated `SpatialGrid` to persist and merge these new fields.
    - Added valid bounds calculation to prevent visualizer distortion.

- **Visualization (`visualize_grid.py`)**:
    - rendering prioritized by Room -> Semantic Layer -> Default.
    - Added specific colors for new layers (Cyan for Low Fence, Orange for High Fence, Red for Wall).
    - Added transparent background support for OBS overlays.


