# 🚀 Project Zomboid Bot Deployment Strategy

This document outlines the architectural options for deploying multiple bot instances ("Survivors") to a server.

## Core Architecture
The bot consists of two components that must run in tandem:
1.  **The Body (Game Client)**: A full instance of `ProjectZomboid64.exe` running the `AISurvivorBridge` Lua mod.
2.  **The Brain (Python Runtime)**: The `bot_runtime` process that reads/writes JSON files to control the Body.

**Communication Channel**:
The bridging occurs via the filesystem in the User's "Cache Directory" (`Zomboid/Lua/AISurvivorBridge`).
*   `state.json`: Body -> Brain
*   `input.json`: Brain -> Body

## Deployment Options

### Option 1: The "Home Lab" (Local Process Fleet)
Run multiple game clients on your local machine or a dedicated Windows server.
*   **Mechanism**:
    *   Launch multiple `ProjectZomboid64.exe` processes.
    *   **CRITICAL**: Each process MUST use a unique `-cachedir` argument (e.g., `-cachedir=C:\BotByron`, `-cachedir=C:\BotAlice`).
    *   This isolates their `Lua/` folders, allowing unique JSON streams for each bot.
    *   Launch corresponding Python Runtimes pointing to those specific directories.
*   **Pros**:
    *   Uses existing hardware.
    *   Zero cost.
    *    easiest to debug (can alt-tab into any bot's window).
*   **Cons**:
    *   High Resource Usage: Each client needs ~2GB RAM and CPU time.
    *   Window Clutter: Multiple game windows (though they can be minimized).
*   **Implementation Effort**: Low. Requires a simple `fleet_manager.py` script.

### Option 2: Containerized Fleet (Docker)
Package the Game Client + Python Runtime into a single Docker image.
*   **Mechanism**:
    *   Base Image: `python:3.11-slim` + `wine` (or Linux native PZ if available/stable).
    *   **Graphics**: Use `Xvfb` (Virtual Framebuffer) to run the game "headless" inside the container.
    *   **Orchestration**: Use `docker-compose` to spin up `bot-1`, `bot-2`, etc.
*   **Pros**:
    *   **Clean Isolation**: No file conflicts guaranteed.
    *   **Portability**: Deploy to any server (AWS, DigitalOcean, local NAS).
    *   **Scalability**: Spin up 50 bots with one command (hardware permitting).
*   **Cons**:
    *   **Performance**: Running 3D games in Docker (software rendering) is slow without GPU passthrough.
    *   **Complexity**: Requires handling SteamCMD authentication inside Docker to download the game.
*   **Implementation Effort**: High. Requires building a robust `Dockerfile` and handling SteamGuard automation.

### Option 3: Distributed Cloud (AWS/GCP)
Spawn separate Virtual Machines for each bot.
*   **Pros**: Infinite horizontal scaling.
*   **Cons**: Very expensive ($$$/hour per GPU instance). Overkill for a personal project.

## Recommendation: Phase 1 - Local Fleet Manager
We should start with **Option 1**. It validates the "Multi-Bot" software architecture without the DevOps overhead of Dockerizing a GUI game immediately.

**Proposed Tooling**:
Create a `tools/fleet_manager.py` CLI:
```bash
python tools/fleet_manager.py spawn --name "Byron" --personality "Brave"
# > Spawns PZ Client (Cachedir: ./data/bots/Byron)
# > Spawns Python Runtime (Config: ./data/bots/Byron/config.json)
```

## Scalable Architecture: The "Pseudo-Headless" Reality
Project Zomboid does NOT have a true "Headless Client" mode. Every bot requires a running Game Client.
To achieve scale (10+ bots) on a server, we must use **Virtual Framebuffers (Xvfb)**.

### Architecture Layering
1.  **Infrastructure**: Docker Containers running `python:3.11-slim` + `wine` + `Xvfb`.
2.  **Squad Orchestration**: A `fleet_manager.py` that reads a `Squad Manifest` (YAML) and spawns the required containers.
3.  **Bot Application**: The standard Client + Brain pair running inside the container.

### Squad Manifests
Groups of bots are defined in `squad_manifest.yaml`. This allows deploying logical units (e.g., "Scavenge Party Alpha") rather than micromanaging individual processes.

### Performance Optimization
Since we cannot disable rendering entirely, we optimally reduce load:
*   Launch Argument: `--noFBO` (Disable offscreen buffers)
*   Launch Argument: `-safemode` (Disable advanced zooming/shaders)
*   In-Game Lua: Force disable 3D models for items/corpses via non-public Java APIs if possible (Research Needed).

## Future Roadmap (Phase 2)
1.  **Local Fleet Manager**: Build `tools/fleet_manager.py` (CLI) to orchestrate local processes.
2.  **Docker Base Image**: Create a `Dockerfile` that packages Wine + PZ + Python.
## Phase 3: The Hive (Persistent Bot Network)
To enable "rejoining" and "memory continuity" across sessions, we must separate the **Survivor Identity** from the **Game Process**.

### Architecture: "The Soul Transfer"
1.  **The Hive (Central Brain)**: A lightweight database (SQLite/Postgres) that stores:
    *   `survivor_id`: Unique UUID.
    *   `personality_genes`: The immutable traits.
    *   `memory_snapshot_path`: Link to the latest `long_term_memory.json`.
    *   `status`: ALIVE, DEAD, MIA.
    *   `server_affinity`: "Last seen on Server X".

2.  **The Lifecycle**:
    *   **Wake Up**: Fleet Manager queries Hive: "Who is deployed to Server A?" -> Downloads `memory.json`.
    *   **Run**: Bot plays, constantly updating its local memory state.
    *   **Sleep (Shutdown)**: On graceful exit, Bot uploads `memory.json` back to Hive.
    *   **Death**: Bot uploads `blackbox.log` to Hive (for Offline Learning) and marks status as DEAD.

3.  **Rejoining**:
    *   User clicks "Deploy Squad" -> Hive checks which survivors are ALIVE and matches them to their previous server.
    *   Bots "wake up" exactly where they left off (mentally), even if the game server was wiped or they moved to a new machine.


