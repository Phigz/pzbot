# Changelog

## [Unreleased]

### Added
-   **Hybrid Input System** (`bot_runtime/input/service.py`):
    -   Implemented `InputService` for abstracting hardware input.
    -   Added `WindowsInputProvider` using `pydirectinput`.
    -   Added `LinuxInputProvider` using `pyautogui` (for Docker/Xvfb).
-   **Lifecycle Manager** (`main.py`):
    -   Unified CLI for Game Launch and Bot Runtime (`--new`, `--continue`, `--join`).
    -   Added `--dev` mode for hot-reloading bot code.
-   **Docker Support**:
    -   Added `Dockerfile` for "Bring Your Own Game" (BYOG) deployment.
    -   Implemented Xvfb virtual display handling.
-   **Multiplayer Support**:
    -   Added `--join <IP>` support to CLI and Launch scripts.
-   **Documentation**:
    -   Added `docs/ARCHITECTURE.md` detailing the Hybrid System and Hive Deployment.
-   **Gameplay Recorder** (`tools/recorder.py`): A tool to capture `state.json` updates to compressed `.jsonl.gz` files for training. Features bookmarking support.
-   **Dream Engine Architecture** (`tools/dream/`): A modular pipeline for processing recordings.
    -   `pipeline.py`: Runner script.
    -   `lib/processor.py`: Base class for plugins.

### Changed
-   **Controller Refactor**: `BotController` now uses `InputService` for physical actions (Attack, Shove, Move) and Lua injection for logical actions.
-   **Launch Scripts**: Updated `launch_pz.bat` and `configure_launch.py` to support argument forwarding (for `-ip`).
