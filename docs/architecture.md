# PZBot System Architecture

This document outlines the high-level architecture of the PZBot, visualizing the flow of information from the game world to the bot's "Brain" and back.

## Conceptual Model

The bot is composed of three primary layers: **The Body** (Lua Mod), **The Mind** (Python Runtime), and **The Debugger** (Web UI).

```mermaid
graph TD
    subgraph Game ["Project Zomboid (The World)"]
        World[Game Engine]
    end

    subgraph Body ["The Body (Lua Mod)"]
        Sensor[Sensor.lua<br>(Eyes & Ears)]
        Motor[ActionExecutor.lua<br>(Hands & Legs)]
    end

    subgraph Mind ["The Mind (Python Runtime)"]
        Ingest[Perception Layer]
        Model[World Model<br>(Memory & Beliefs)]
        Analyze[Derived Analysis<br>(Threats & Resources)]
        Brain[Decision Engine<br>(Goals & Strategy)]
        Planner[Action Planner]
    end

    subgraph Debug ["Debugger (Observability)"]
        Visualizer[Web Visualizer]
    end

    World -- "Light, Sound, Signals" --> Sensor
    Sensor -- "state.json" --> Ingest
    Ingest --> Model
    Model --> Analyze
    Analyze --> Brain
    Brain -- "High-Level Intent" --> Planner
    Planner -- "input.json" --> Motor
    Motor -- "API Calls" --> World
    
    Model -.-> Visualizer
    Analyze -.-> Visualizer
```

## Detailed Data Flow

### 1. Perception (Input)
The "Sensory" layer handles the raw ingestion of game data.

```text
[ WORLD ] 
    |
    | (Light / Sound / Radio)
    v
[ BODY (Lua) ] 
    | • Visual Scan (Tiles, Objects)
    | • Audio Scan (Footsteps, Bangs)
    | • Signal Scan (Radio Broadcasts)
    |
    | (state.json)
    v
[ PERCEPTION (Python) ]
    |
    v
[ WORLD MODEL ]
    | • SpatialGrid: "Where are the walls?"
    | • EntityTracker: "Where are the zombies?"
    | • NoiseMap (Planned): "Where did I hear that sound?"
    | • SignalBuffer (Planned): "What did the radio say?"
```

### 2. Analysis (Processing)
Once the world is modeled, we derive higher-level understanding.

```text
[ WORLD MODEL ]
    |
    v
[ DERIVED ANALYSIS ]
    | • ThreatMap: Heatmap of danger zones (Line of Sight + Noise)
    | • ResourceMap: Known food/weapon locations
    | • SurvivalState: Hunger, Thirst, Fatigue projections
```

### 3. Decision (Output)
The "Brain" uses the analyzed world to make choices.

```text
[ DERIVED ANALYSIS ]
    |
    v
[ DECISION ENGINE ]
    | • Goal: "Survive" -> "Find Food"
    | • Strategy: "Avoid High Threat Areas"
    |
    v
[ ACTION PLANNER ]
    | • "Go to Kitchen" -> [Pathfind, Open Door, Walk]
    |
    | (input.json)
    v
[ BODY (Lua) ] --> [ ACTUATE ]
```
