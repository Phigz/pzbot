# Project Zomboid Bot (AISurvivor)

An autonomous agent for Project Zomboid using a Hybrid Python/Lua architecture.

## Quickstart

### Prerequisites
-   **Project Zomboid** (Steam ver.) installed.
-   **Python 3.10+**

### Running the Bot (Docker / "The Hive")
This is the recommended way to run the bot. It uses a **Persistent Hive** architecture where multiple bots share a single game installation on your host machine.

#### 1. Start the Hive
```bash
docker-compose up
```
This will:
1.  Launch the **PZ Game Client** (headless-ish).
2.  Start the **Bot Brain**.
3.  Hot-reload code changes automatically.

#### 2. Spawning Multiple Bots
To spawn additional bots that join the same server/world:
```bash
docker-compose run --rm pz-bot python main.py --join <SERVER_IP>
```

### Maintenance

#### Cleaning Up
If you previously ran the bot with the old config, you may have a large `./zomboid-cache` folder. You can safely delete this folder to reclaim disk space, as the game data is now stored in a Docker Named Volume.

#### Resetting Game Data
To completely wipe the game installation and force a fresh download:
```bash
docker volume rm pzbot_pz-game-install
```

### Development Workflow
We have optimized the workflow for rapid iteration.

#### Python (Bot Logic)
- **Hot-Reloading**: Enabled by default in `docker-compose`.
- **How**: Edit any file in `pzbot/`. The bot runtime will detect the change and restart the "Brain" process immediately. The Game Client **stays running**, so you don't lose your spot.

#### Lua (Game Logic)
- **Hot-Reloading**: Edit files in `mods/AISurvivorBridge`.
- **Apply**: In the game console (if visible) or via `debug_bot.py` (future), trigger a Lua reload. *Note: Fully automated Lua hot-reloading is a WIP.*

#### Debugging
- Access the Debug Dashboard at `http://localhost:8000` (if running `debug_bot.py`).
