import heapq
from typing import Callable, List, Tuple
from .state_factory import StateFactory
import math

class MockWorld:
    def __init__(self):
        # Initialize with a clean state structure
        self.state = StateFactory.create_default_state()
        
        # Internal Sim Variables
        self.player_x = 100.0
        self.player_y = 100.0
        self.player_z = 0
        self.tick_count = 0
        
        # Timeline / Simulation Time
        self.sim_time = 0.0
        self.end_time = None # If None, runs indefinitely until manual stop
        self.event_queue: List[Tuple[float, Callable]] = []
        
        # World Data
        self.grid = {} # (x, y) -> Tile Dict
        
        # Simple list of Zombies: {"id": "z1", "x": 105, "y": 100, "state": "idle"}
        self.zombies = []

    def update(self, dt_seconds):
        self.tick_count += 1
        self.sim_time += dt_seconds
        
        self.state["tick"] = self.tick_count
        self.state["timestamp"] += int(dt_seconds * 1000)
        
        # Process Events
        while self.event_queue and self.event_queue[0][0] <= self.sim_time:
            _, callback = heapq.heappop(self.event_queue)
            callback()
        
        # Update Player Position in State
        self.state["player"]["position"]["x"] = self.player_x
        self.state["player"]["position"]["y"] = self.player_y
        self.state["player"]["position"]["z"] = self.player_z
        
        # Update Vision Radius
        scan_radius = self.state["player"]["vision"]["scan_radius"]
        
        # Render Tiles
        visible_tiles = []
        min_x = int(self.player_x - scan_radius)
        max_x = int(self.player_x + scan_radius)
        min_y = int(self.player_y - scan_radius)
        max_y = int(self.player_y + scan_radius)
        
        for tx in range(min_x, max_x + 1):
            for ty in range(min_y, max_y + 1):
                # Check distance simply (square or circle, doing square for simplicity here or could do circle)
                # Using simple square check aligned with loop for now.
                
                # If tile is defined in grid, use it. Else default to Floor.
                tile_key = (tx, ty)
                if tile_key in self.grid:
                    t_data = self.grid[tile_key].copy()
                    t_data["x"] = tx
                    t_data["y"] = ty
                    t_data["z"] = 0
                    visible_tiles.append(t_data)
                else:
                    # Default floor
                    visible_tiles.append({
                        "x": tx, "y": ty, "z": 0,
                        "room": "outside",
                        "layer": "Floor",
                        "w": True
                    })
        
        self.state["player"]["vision"]["tiles"] = visible_tiles
        
        # Render visible objects
        visible_objects = []
        for z in self.zombies:
            dist = math.sqrt((z["x"] - self.player_x)**2 + (z["y"] - self.player_y)**2)
            if dist <= scan_radius:
                visible_objects.append({
                    "id": z["id"],
                    "type": "Zombie",
                    "x": z["x"],
                    "y": z["y"],
                    "z": 0,
                    "meta": { "state": z["state"] }
                })
        
        self.state["player"]["vision"]["objects"] = visible_objects

    def set_tile(self, x, y, layer="Floor", room="outside", walkable=True):
        self.grid[(x, y)] = {
            "layer": layer,
            "room": room,
            "w": walkable
        }

    def set_player_pos(self, x, y):
        self.player_x = float(x)
        self.player_y = float(y)

    def add_zombie(self, x, y, uid="z1"):
        self.zombies.append({"id": uid, "x": x, "y": y, "state": "idle"})
        
    def add_event(self, at_time: float, action: Callable):
        """Schedule an action (callable) to run at specfic sim_time"""
        heapq.heappush(self.event_queue, (at_time, action))
        
    def set_end_time(self, t: float):
        self.end_time = t
        
    def is_finished(self):
        if self.end_time is not None:
            return self.sim_time >= self.end_time
        return False
        
    def get_state_snapshot(self):
        return self.state
