# PZ Bot Architecture

## High-Level Overview
The PZ Bot is a **Hybrid Agent** that bridges a high-level Python Brain with the low-level Project Zomboid Lua API.

It uses a dual-channel communication system:
1.  **Perception (Lua -> Python)**: The game state is serialized to JSON by Lua and read by Python.
2.  **Actuation (Python -> Game)**:
    -   **Direct Input**: Movement and Combat are sent as hardware-level keystrokes (DirectX).
    -   **Lua Injection**: Inventory, Crafting, and UI interactions are sent as JSON commands to Lua.

## 1. Input System (Hybrid)
We use a **Hybrid Input Architecture** to get the best of both worlds:
-   **Precision**: `pydirectinput` (Windows) or `xdotool` (Linux) provides analog-like control for walking and fighting.
-   **Reliability**: Lua injection ensures atomic inventory operations (e.g. transfer item) without relying on fragile UI clicking.

### Input Service (`bot_runtime.input.service`)
The `InputService` abstracts the OS differences.
-   **Windows**: Uses `pydirectinput`.
-   **Linux**: Uses `xdotool` (via Docker/Xvfb).

## 4. Docker Strategy (The "Hive")

We utilize a **Persistent Hive** architecture to allow scalable, efficient bot deployment.

### A. The "Game Cartridge" (Volume)
Instead of embedding the 4GB+ game inside the image, we use a **Docker Volume** on the host machine (`./zomboid-cache`).
- **Initial Run**: Downloads the game to the host volume.
- **Subsequent Runs**: Mounts the volume. 0-second install time.

### B. Deployment
```bash
docker-compose up --scale pz-bot=3
```
This spawns 3 bot containers, all sharing the *single* game installation on disk.

### C. Hybrid Execution
- **Game**: Runs via Wine (simulated Windows environment) inside Linux container.
- **Bot**: Runs native Python in the same container.
- **Communication**: Shared filesystem and local network (localhost).

## 5. Lifecycle Manager (`main.py`)
The `main.py` script orchestrates the entire stack.
-   **`--new`**: Starts a fresh game session.
-   **`--continue`**: Resumes the last save.
-   **`--dev`**: Watching file system for code changes and hot-restarts the Bot Brain without closing the game.
-   **`--join <IP>`**: Joins a multiplayer server directly.
