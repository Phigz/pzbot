import time

class StateFactory:
    @staticmethod
    def create_default_state():
        """
        Returns a dictionary strictly adhering to docs/schemas/output_state.json
        """
        current_time = int(time.time() * 1000)
        return {
            "timestamp": current_time,
            "tick": 0,
            "player": {
                "status": "idle",
                "vitals": {
                    "health": 100.0,
                    "stamina": 1.0,
                    "hunger": 0.0,
                    "panic": 0.0
                },
                "active_action_id": "",
                "position": {
                    "x": 100.0,
                    "y": 100.0,
                    "z": 0
                },
                "rotation": 0.0,
                "state": {
                    "aiming": False,
                    "sneaking": False,
                    "running": False,
                    "sprinting": False,
                    "in_vehicle": False,
                    "is_sitting": False,
                    "asleep": False,
                    "moving": False,
                    "driving": False,
                    "bumped": False,
                    "climbing": False,
                    "attacking": False
                },
                "body": {
                    "health": 100.0,
                    "temperature": 37.0,
                    "parts": {
                        "Head": { "health": 100.0, "bandaged": False, "bleeding": False, "bitten": False, "scratched": False, "deep_wound": False, "pain": 0.0, "stitch": False, "burn": False, "fracture": False, "glass": False, "splinted": False, "bullet": False, "infection": 0.0 },
                        "Torso_Upper": { "health": 100.0, "bandaged": False, "bleeding": False, "bitten": False, "scratched": False, "deep_wound": False, "pain": 0.0, "stitch": False, "burn": False, "fracture": False, "glass": False, "splinted": False, "bullet": False, "infection": 0.0 },
                        "Hand_L": { "health": 100.0, "bandaged": False, "bleeding": False, "bitten": False, "scratched": False, "deep_wound": False, "pain": 0.0, "stitch": False, "burn": False, "fracture": False, "glass": False, "splinted": False, "bullet": False, "infection": 0.0 },
                        "Hand_R": { "health": 100.0, "bandaged": False, "bleeding": False, "bitten": False, "scratched": False, "deep_wound": False, "pain": 0.0, "stitch": False, "burn": False, "fracture": False, "glass": False, "splinted": False, "bullet": False, "infection": 0.0 },
                        "Leg_L": { "health": 100.0, "bandaged": False, "bleeding": False, "bitten": False, "scratched": False, "deep_wound": False, "pain": 0.0, "stitch": False, "burn": False, "fracture": False, "glass": False, "splinted": False, "bullet": False, "infection": 0.0 },
                        "Leg_R": { "health": 100.0, "bandaged": False, "bleeding": False, "bitten": False, "scratched": False, "deep_wound": False, "pain": 0.0, "stitch": False, "burn": False, "fracture": False, "glass": False, "splinted": False, "bullet": False, "infection": 0.0 }
                    }
                },
                "moodles": {},
                "traits": [],
                "skills": {},
                "profession": "unemployed",
                "attached": {},
                "equipped": {},
                "inventory": {},
                "vision": {
                    "scan_radius": 15,
                    "timestamp": current_time,
                    "tiles": [],
                    "objects": [],
                    "neighbors": {
                        "n": { "x": 100, "y": 99, "status": "walkable", "objects": [] },
                        "s": { "x": 100, "y": 101, "status": "walkable", "objects": [] },
                        "e": { "x": 101, "y": 100, "status": "walkable", "objects": [] },
                        "w": { "x": 99, "y": 100, "status": "walkable", "objects": [] }
                    }
                }
            },
            "environment": {
                "nearby_containers": []
            },
            "events": []
        }
