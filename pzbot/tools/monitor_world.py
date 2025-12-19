import sys
import time
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from bot_runtime import config
from bot_runtime.ingest.watcher import StateWatcher
from bot_runtime.world.model import WorldModel
from bot_runtime.ingest.state import GameState

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

class WorldMonitor:
    def __init__(self):
        self.world_model = WorldModel()
        self.last_update_time = time.time()
        self.updates_received = 0

    def on_tick(self, game_state: GameState):
        """Callback for state updates."""
        self.world_model.update(game_state)
        self.updates_received += 1
        self.last_update_time = time.time()
        self.render_dashboard()

    def render_dashboard(self):
        """Prints the dashboard to stdout."""
        # Use simple print with clear screen for now (flicker is acceptable for MVP)
        clear_screen()
        
        wm = self.world_model
        p = wm.player
        
        if not p:
            print("Waiting for player state...")
            return

        now_str = datetime.now().strftime("%H:%M:%S")
        
        print(f"=== PZBOT WORLD MONITOR [{now_str}] ===")
        print(f"Updates: {self.updates_received} | Last Delta: {(time.time() - self.last_update_time):.3f}s")
        print("-" * 40)
        
        # Player Stats
        print(f"[PLAYER]")
        print(f"  Pos : ({p.position.x:.1f}, {p.position.y:.1f}, {p.position.z})")
        print(f"  Rot : {p.rotation:.1f}")
        print(f"  Stat: {p.action_state.status} (Seq: {p.action_state.sequence_number})")
        
        # World Map Stats
        grid_size = len(wm.map.grid)
        print(f"[WORLD MAP]")
        print(f"  Total Tiles: {grid_size}")
        print(f"  Bounds     : [{wm.map.min_x}, {wm.map.min_y}] -> [{wm.map.max_x}, {wm.map.max_y}]")
        
        # Entity Stats
        entities = wm.entities.entities
        zombies = [e for e in entities.values() if e.type == 'Zombie']
        items = [e for e in entities.values() if e.type != 'Zombie' and 'Player' not in e.type]
        
        print(f"[ENTITIES]")
        print(f"  Tracked : {len(entities)}")
        print(f"  Zombies : {len(zombies)}")
        print(f"  Items   : {len(items)}")
        
        if zombies:
            nearest = min(zombies, key=lambda z: ((z.x - p.position.x)**2 + (z.y - p.position.y)**2))
            dist = ((nearest.x - p.position.x)**2 + (nearest.y - p.position.y)**2)**0.5
            print(f"  Nearest Z: {dist:.1f}m (ID: {nearest.id[:6]}...)")

    def run(self):
        print("Initializing Monitor...")
        watcher = StateWatcher(
            state_file_path=config.STATE_FILE_PATH,
            on_update=self.on_tick,
            polling_interval=0.1
        )
        
        try:
            watcher.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nMonitor stopped.")
            watcher.stop()
        except Exception as e:
            print(f"Error: {e}")
            watcher.stop()

if __name__ == "__main__":
    monitor = WorldMonitor()
    monitor.run()
