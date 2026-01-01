# World Model Schemas: Live vs. Memory

This document defines the two primary data models used in the bot's world representation: **Live Data** (Observations) and **Memory Data** (Beliefs).

## 1. Live Data (Observation)
**Source**: Lua Game State (`state.json`) -> `Sensor.lua`
**Context**: "What the bot sees *right now*."
**Characteristics**:
- **Transient**: Exists only for the current tick.
- **Truthful**: Direct extraction from game engine.
- **Nested Metadata**: Entity-specific properties are stored in a `meta` dictionary.

### Schema (JSON Structure)
```json
{
  "id": "string",           // Unique ID (e.g., "33", "player_0")
  "type": "string",         // "Animal", "Zombie", "Player", "Vehicle"
  "x": "number",            // Raw World Coordinate
  "y": "number",
  "z": "number",
  "meta": {                 // <--- NESTED Container for specialized data
    "species": "string",
    "breed": "string",
    "age": "number",
    "health": "number",
    "hunger": "number",     // (Experimental)
    "isFemale": "boolean",
    "worn": ["string"],     // List of worn items (Zombies/Players)
    "dist": "number"        // Distance from observer
  }
}
```

### Signal Schema (Environmental)
**Source**: `vision.signals` in `state.json`
**Context**: "Radio and TV broadcasts detected nearby."
```json
{
  "type": "string",         // "Radio", "TV"
  "name": "string",         // e.g. "Premium Technologies Radio"
  "x": "number",
  "y": "number",
  "z": "number",
  "on": "boolean",          // Is powered on
  "channel": "number",      // Frequency/Channel
  "volume": "number",       // 0.0 - 1.0
  "msg": "string"           // Last broadcast message or Media Title (e.g. "Media: Cooking Show")
}
```

---

## 2. Memory Data (Belief)
**Source**: Python Runtime (`grid_snapshot.json`) -> `MemorySystem`
**Context**: "What the bot *remembers* about the world."
**Characteristics**:
- **Persisted**: Retained across ticks (until decay).
- **Decayed**: Contains `last_seen` and `ttl_remaining_ms`.
- **Flattened**: Specialized properties are merged into the root object to simplify querying and serialization.

### Schema (JSON Structure)
```json
{
  "id": "string",           // Same Unique ID
  "type": "string",         // Same Type
  "x": "number",            // Last known position
  "y": "number",
  "z": "number",
  
  // Tracking Fields
  "last_seen": "number",        // Timestamp (ms)
  "ttl_remaining_ms": "number", // Time until forgotten
  "is_visible": "boolean",      // Inherited from visibility check
  
  // <--- FLATTENED Properties (Merged from Live `meta`)
  "species": "string",
  "breed": "string",
  "age": "number",
  "health": "number",
  "isFemale": "boolean",
  "hunger": "number",
  "worn": ["string"]
}
```

## 3. Transformation Rules
The transition from **Live** to **Memory** occurs in `MemorySystem._wrap_data`.

1.  **Ingestion**: The system receives a `Live` object.
2.  **Extraction**: It extracts `id`, `type`, and coordinates.
3.  ** flattening**: 
    - The contents of `Live.meta` are implicitly merged into the root `properties` of the internal `EntityData` model.
    - When serialized to `grid_snapshot.json`, these properties appear at the top level of the JSON object.
4.  **Decay Management**: `last_seen` is updated. If the object is not seen for `TTL` duration (depends on type), it is removed from memory.

## 4. Usage Guide
- **Bot Logic (Decision Making)**: Should primarily query **Memory** (`MemorySystem`) to have a stable view of the world (including things behind the agent).
- **Debugging / Visualization**: 
    - **Live View**: Renders raw `state.json`. Must handle `meta` nesting.
    - **Memory View**: Renders `grid_snapshot.json`. Must handle flattened properties.
