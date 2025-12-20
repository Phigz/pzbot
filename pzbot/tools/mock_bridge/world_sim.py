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
        
        # Simple list of Zombies: {"id": "z1", "x": 105, "y": 100, "state": "idle"}
        self.zombies = []

    def update(self, dt_seconds):
        self.tick_count += 1
        self.state["tick"] = self.tick_count
        self.state["timestamp"] += int(dt_seconds * 1000)
        
        # Update Player Position in State
        self.state["player"]["position"]["x"] = self.player_x
        self.state["player"]["position"]["y"] = self.player_y
        self.state["player"]["position"]["z"] = self.player_z
        
        # Update Vision Radius
        scan_radius = self.state["player"]["vision"]["scan_radius"]
        
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

    def set_player_pos(self, x, y):
        self.player_x = float(x)
        self.player_y = float(y)

    def add_zombie(self, x, y, uid="z1"):
        self.zombies.append({"id": uid, "x": x, "y": y, "state": "idle"})
        
    def get_state_snapshot(self):
        return self.state
