# 🐝 The Hive: System Architecture & Feasibility Analysis

This document outlines the practical implementation of "The Hive" — the central nervous system for a persistent Bot Network.

## 1. Core Distinction: Control Plane vs. Compute Plane
The most important concept is that **The Hive is NOT the game server.**

*   **The Hive (Control Plane)**: Very lightweight. It's just a web server and a database.
    *   *Role*: Stores Bot IDs, Personality DNA, and Memory Files (JSON).
    *   *Hardware*: Can run on a Raspberry Pi or AWS `t3.nano` ($3/month).
    *   *Resource Usage*: Negligible CPU/RAM.
*   **The Drone Fleet (Compute Plane)**: Very heavy. This is where `ProjectZomboid64.exe` runs.
    *   *Role*: Simulates the game world and physics.
    *   *Hardware*: Needs Gaming PC or Heavy Cloud GPU instances (`g4dn.xlarge`).
    *   *Resource Usage*: ~2GB RAM + 1 vCPU **per bot**.

**Conclusion**: You can host the "Hive" globally for pennies. It's the *Bots* that require the heavy iron.

---

## 2. Practical Implementation Models

### Model A: "The Local Laboratory" (Development / Home Lab)
*   **Infrastructure**: All running on *your* desktop.
*   **Hive Stack**:
    *   **Database**: SQLite file (`hive.db`).
    *   **API**: Python Script (FastAPI) running on port 8000.
    *   **Storage**: Local folder `C:\BotHive\Memories\`.
*   **Pros**: Zero latency, free, simplest to build.
*   **Cons**: If your PC dies, the Hive dies. Limited by your PC's RAM (max ~8-10 bots).

### Model B: "The Distributed Network" (Production Vision)
*   **Infrastructure**:
    *   **Hive Server**: AWS EC2 `t4g.micro` (Cheap web server).
    *   **Bot Node 1**: Your PC (Hosting "Home Base Squad").
    *   **Bot Node 2**: A Spare Laptop (Hosting "Scout Squad").
    *   **Bot Node 3**: A friend's PC (Hosting "Support Squad").
*   **How it Works**:
    1.  Your PC launches a bot.
    2.  Bot queries `https://api.my-hive.com/survivor/spawn`.
    3.  Hive says: "Spawning 'Rick'. Here is his memory file."
    4.  Your PC downloads the 5MB JSON and starts the game.
    5.  When 'Rick' sleeps, your PC uploads the updated JSON back to the Hive.
*   **Pros**: Infinite scaling. You can add more "Nodes" (computers) to run more bots without upgrading the Hive.
*   **Cons**: Network latency (uploading 5MB saves), complexity of auth/security.

---

## 3. The Tech Stack (Realistic Choice)

For a robust "Phase 2" implementation, we should generally use standard, proven web technologies:

*   **API Framework**: **FastAPI** (Python). Fast, auto-documents with Swagger.
*   **Database**: **PostgreSQL** (or SQLite for start). Relational data is best for "Roster" management.
*   **Blob Storage**: **MinIO** (Self-hosted S3). Essential for storing the *Memory Files* and *Replays*. Don't store files in the database!
*   **Auth**: **API Keys**. Each "Fleet Manager" (Compute Node) has a key to talk to the Hive.

---

## 4. Real-World Complications & Risks

### A. The "Zombie State" Dilemma (Desync)
**Scenario**: Bot A runs on Node 1. Node 1 crashes (BSOD). The Hive thinks Bot A is still "ALIVE".
**Fix**: Heartbeats. Bot A must ping Hive every 30s. If pings stop for 2 mins, Hive marks Bot A as "MIA" (Missing in Action).

### B. "Bad Memories" (Versioning)
**Scenario**: You update the Game Code (Add new items). Bot A uploads a memory file containing "MegaRifle". Later, you roll back the update. Bot B tries to download "MegaRifle" into an older client -> **CRASH**.
**Fix**: Semantic Versioning. Hive must track `game_version` for every memory snapshot. "Rick is compatible with v41.78+".

### C. Bandwidth is the Bottleneck
**Scenario**: You spawn a squad of 10 bots. That's 10 simultaneous downloads of memory/map data.
**Reality**: 5MB * 10 = 50MB. Fast on LAN, slow on AWS if not careful.
**Optimization**: Incremental Sync. Only upload the *diffs* of the memory, not the full file every time.

---

## 5. The "Clone & Run" Vision (Consumer Product)

The goal is to make this a **Single Command Deploy** for any PZ player.

**User Workflow**:
1.  `git clone pz-hive-mind`
2.  `./start_hive.sh` (Starts the Web UI + Database).
3.  **UI Opens**: "Welcome to the Hive. Enter your PZ Server IP (e.g., 127.0.0.1:16261)".
4.  **Connect**: Hive verifies RCON connection to the Game Server.
5.  **Dashboard**: User sees "Active Survivors" (from previous runs) and "Recruitment Pool".
6.  **Action**: User clicks "Deploy Alpha Squad".
    *   Hive spins up 4 local bot processes.
    *   Bots auto-join the game server.
    *   Hive monitors them and updates the Web UI.

### The "Sidecar" Architecture
In this model, the **Hive** is a standalone local service that acts as a **Launcher + Database**.
*   **Database**: A simple `hive.db` (SQLite) inside the repo.
*   **Networking**: It assumes the Game Server is on `localhost` or LAN.
*   **No Cloud Required**: Everything is contained in the folder. To "transfer" a soul, you just copy the `.db` file.

### Resource Reality Check
*   **The Hive Process**: ~50MB RAM. (Tiny. Run it anywhere).
*   **The Bot Process**: ~2GB RAM *Per Bot*. (Heavy. Runs on your Gaming PC).
*   **Conclusion**: You do **NOT** need a separate server/cloud host. You just need enough RAM on your PC for the number of bots you want to play with.


