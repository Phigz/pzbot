# Changelog

All notable changes to the PZBot project will be documented in this file.

## [0.3.0] - 2025-12-31

### Auditory & Signal Perception
- **Lua Perception Layer**:
    - **Radio & TV Integration**: Robust probing of `ZomboidRadio` and `DeviceData`.
    - **Signal Extraction**: Extracts `Channel`, `Volume`, `IsOn`, and broadacst `MediaData` (Message/Title) from nearby devices.
    - **Performance**: Optimized scanning to avoid crashes with `SafeExtract` protection.

- **Python Memory System**:
    - **Persistence**: Signals are now treated as persistent memory objects with a 30-second TTL (simulating memory of a broadcast).
    - **Grid Snapshot Upgrade**: Fixed logic to correctly merge external Entity/Signal data into the `grid_snapshot.json`.

- **Debugger Visualization (v2.0)**:
    - **Grouped UI**: Live and Memory tabs now grouped by `Zombie`, `Animal`, `Player`, `Interactable`, and `Signal`.
    - **Signal Visualization**: Audio signals (Radio/TV) visualized as concentric rings (Blue=TV, Green=Radio) with message overlays.
    - **TTL Indicators**: Visualization of decaying memory for signals and entities.
    - **Cleanup**: Removed legacy visualization scripts (`visualize_grid.py`, `map_view.html`).

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


