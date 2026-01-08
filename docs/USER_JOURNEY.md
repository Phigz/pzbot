# 🌅 The Morning Routine: A User Journey

This document visualizes the exact experience of using the Hive, answering "Where does it run?" and "What do I click?".

## Scenario: The "All-in-One" Local Player
**setup**: You have one powerful PC. You want to play legally, and have 3 bots join you.
**Hardware**: Your Gaming PC (No EC2, No Raspberry Pi required).

### Step 1: Wake Up & Coffee ☕
You sit down at your PC.

### Step 2: Host the World 🌍
1.  Launch **Project Zomboid** normally via Steam.
2.  Click **Host** -> **Manage Settings** -> **Start Server**.
3.  You spawn in as "Lucas" (The Human).
    *   *Status*: You are in-game, alone. The world is live.

### Step 3: Wake the Hive 🐝
1.  `Alt-Tab` out of the game.
2.  Open a Terminal (PowerShell).
3.  Run: `python tools/start_hive.py`
    *   *What happens*: A small web server starts (Uses ~50MB RAM).
    *   *Output*: `Hive Interface active at http://localhost:8000`

### Step 4: Deploy the Squad 🚀
1.  Open Chrome to `http://localhost:8000`.
2.  You see the **Dashboard**:
    *   **Server**: "Detected Local Server (127.0.0.1)"
    *   **Squads**: "Alpha Team (3 Members) - Status: ASLEEP"
3.  Click the big green **[WAKE UP]** button.

### Step 5: The Arrival 🪂
1.  *Behind the scenes*: The Hive executes the **Fleet Manager**.
2.  **3 New Windows Open**:
    *   Three minimized `ProjectZomboid64.exe` windows launch.
    *   Three `bot_runtime` consoles appear.
3.  `Alt-Tab` back to your main game.
4.  **In-Game Message**: "Rick joined the game.", "Daryl joined the game.", "Glenn joined the game."
5.  You see them walk out of the safehouse bedroom (where they logged off yesterday).
6.  **"Let's roll."**

---

## FAQ: Resource & Architecture

### "Do I need an EC2 or Raspberry Pi?"
**NO.**
*   **The Hive**: Uses less RAM than a single Chrome tab. It runs in the background on your PC effortlessly.
*   **The Bots**: These are heavy. Each one is a full game instance. Your PC limits how many you can run (typically 3-4 bots per 16GB RAM).

### "When would I use a second computer?"
Only if your main PC is too slow to run 5 copies of the game at once.
*   **Scenario**: You have a gaming PC (You) and an old laptop (Bots).
*   **Setup**: Run `start_hive.py` on the **Laptop**. It spawns the bots on the *Laptop*, but they connect to the server hosted on your *Gaming PC* via LAN.

### "Does the Hive 'resume' them?"
**Yes.**
*   When you clicked **[WAKE UP]**, the Hive looked up "Rick" in its database.
*   It found `Rick_Memory_Day100.json`.
*   It injected that memory into the new process.
*   Rick "wakes up" knowing he was hungry and needs to organize the loot.
