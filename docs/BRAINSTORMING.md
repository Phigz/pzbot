# 🧠 Brainstorming & Concept Lab

This document serves as a catchment area for high-level ideas, feature concepts, and architectural experiments.

---

## 🤖 Bot Framework (The Brain)
*Core logic, decision making, and control architecture.*

### 1. Hybrid Control / Auto-Pilot ("The Co-Pilot Model")
*   **What**: A Control Gate that toggles between "Observer" (Passive logging) and "Actor" (Active input) modes.
*   **Why**: Allows the user to play the game while the bot "backseat games" via the debugger, verifying its logic without risking the character.

### 2. Personality & Behavioral Modifiers
*   **What**: Use traits like **Bravery** (threat tolerance), **Greed** (loot priority), and **Caution** (unknown area avoidance) as coefficients in utility calculations.
*   **Why**: Decouples logic from behavior. A "Cowardly" bot and a "Brave" bot share the same code but make vastly different choices.

### 3. "Black Box" Death Recorder
*   **What**: A ring buffer that dumps the last 60 seconds of State, Vision, and Decisions to a file upon Player Death.
*   **Why**: Essential forensics. Understanding a death loop is impossible if the data is lost the moment the game over screen appears.

### 4. Utility-Based Needs System
*   **What**: Replace static thresholds (`if hunger > 10`) with non-linear utility curves (Sigmoid/Exponential).
*   **Why**: Creates organic urgency. The difference between 10% and 15% hunger is negligible, but 80% to 85% should drastically spike the "Find Food" priority.

### 5. Confidence-Based Skill Learning
*   **What**: The bot tracks its own action outcomes (e.g., "I missed my last 3 shoves").
*   **Why**: Simulates psychological "Confidence". A bot on a losing streak should play more defensively, while a successful one gains momentum.

---

## 🛠️ Debugger & Observability (The Eyes)
*Web UI, visualization, and monitoring tools.*

### 1. "Inner Monologue" Console
*   **What**: A scrolling text log in the Web UI displaying the "Thought Stream" (Percept -> Analysis -> Decision).
*   **Why**: Detailed text logs explain *why* a decision was made better than a visual map ever could.

### 2. Interactive Command Map
*   **What**: Ability to Right-Click on the Canvas Map to issue context commands (e.g., "Force Move Here", "Inspect This").
*   **Why**: Accelerates pathfinding testing. You don't need to wait for the bot to *want* to go somewhere to test if it *can* get there.

### 3. Session Replay ("The VCR")
*   **What**: Record the `grid_snapshot` stream to a file and allow the Debugger to load and "scrub" through the timeline.
*   **Why**: Debugging real-time combat is hard. Being able to pause, rewind, and inspect the state frame-by-frame is a game changer.

### 4. Time-Series Telemetry (Dashboards)
*   **What**: Live graphs plotting key metrics (Health, Panic, Threat Level, Zombie Count) over the last 5 minutes.
*   **Why**: Helps spot trends and correlations, e.g., "Panic spikes 3 seconds before every pathfinding failure."

### 5. Decision Graph Inspector
*   **What**: A visual node graph representing the current Logic Tree or Goal Hierarchy (GOAP/HTN).
*   **Why**: Visually highlights which branches were considered and rejected. "Why didn't it loot the gun? Oh, the 'Has Backpack' precondition failed."

---

## 🎮 Mod & Game Bridge (The Body)
*Lua scripts, in-game rendering, and supplemental mods.*

### 1. In-Game Intent Overlays
*   **What**: Render floating text above the character's head in-game showing current State/Target (e.g., "RETREATING").
*   **Why**: Provides immediate feedback during gameplay without needing to look at a second monitor.

### 2. "The Cartographer" (Static Map Dumper)
*   **What**: A separate, standalone mod or startup script that dumps the game's static collision geometry (Walls, Windows) to a file.
*   **Why**: Pre-seeds the `SpatialGrid`. The bot shouldn't have to "discover" that a house has walls; it should know the static world and only focus on dynamic threats.

### 3. "Scenario Director"
*   **What**: A mod exposing an API to spawn entities (Zombies, Items) at specific coordinates.
*   **Why**: Enables automated Integration Tests. We can script a "Combat Test" where we spawn 5 zombies nearby and measure the bot's survival rate.

### 4. Visual Debug Lines (Vision Cones)
*   **What**: Render 3D lines in the game world showing the bot's raycasts and exact vision sector.
*   **Why**: Instantly distinguishes between "Bot didn't look there" (Perception) vs "Bot ignored it" (Logic).

### 5. Contextual Event Broadcasting
*   **What**: An event-driven queue in `state.json` for transient game events (e.g., "Glass Shattered", "Bite Received").
*   **Why**: Polling every 100ms might miss a frame-perfect event. An explicit event logs ensures the Python brain catches every critical sound or injury.

---

## 🧠 Session: January 2026 (Expansion Pack)
*New ideas focused on Offline Learning, Advanced Analysis, and "Side-Quests".*

### 1. Offline Learning / Memory Consolidation ("The Dream")
*   **Concept**: A standalone analyzer that runs between game sessions (or when the bot is "sleeping").
*   **Mechanism**:
    *   Parse `blackbox.log` and session recordings.
    *   Identify "Death Locations" and "Resource Hotspots".
    *   Update a persistent `long_term_memory.json` that biases future pathfinding (e.g., "Avoid the Mall entrance, I died there 3 times").
*   **Goal**: Create a sense of evolving wisdom that persists across reboots.

### 2. Tactical Geometry Analyzer (Combat Side-Quest)
*   **Concept**: A dedicated math module for real-time tactical analysis.
*   **Features**:
    *   **Choke Point Detection**: Identify doorways/hallways as high-value combat zones.
    *   **Flank Awareness**: Calculate zombie vectors to detect encirclement before it happens.
    *   **Kiting Lanes**: Pre-calculate clear escape routes for "fighting while retreating".

### 3. The "Base Manager" Strategy
*   **Concept**: A specialized high-level strategy for when the bot finds a "Safe House".
*   **Activities**:
    *   **Inventory Sort**: Move food to fridge, weapons to cupboards.
    *   **Barricading**: Detect windows and apply planks.
    *   **Maintenance**: Clean blood, turn off lights to save power.
*   **Why**: Adds "cozy" human-like behavior and utility beyond just surviving.

### 4. Genetic Tuning ("Darwin's Bot")
*   **Concept**: Use the **Scenario Director** to run automated combat trials with varying parameters (e.g., Aggression 0.5 vs 0.8).
*   **Goal**: Automatically find the optimal tuning for specific scenarios (e.g., "What is the best retreat distance for a Horde of 10?").

### 5. "The Compass" (Exploration Heuristic)
*   **Concept**: A heatmap-based exploration driver.
*   **Mechanism**:
    *   Divide the world into chunks.
    *   Track "Time Since Last Visit" for each chunk.
    *   Drive the bot to "Stale" chunks to ensure the map is kept up-to-date.

### 6. External "Mission Control" Dashboard
*   **Concept**: A separate Python web app (Dash/Streamlit) for post-session analysis.
*   **Metrics**:
    *   Survival Time averages.
    *   Kill/Death ratios.
    *   Resource gathering efficiency (Calories found per hour).
