import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from bot_runtime.world.model import WorldModel
from bot_runtime.ingest.state import GameState

def create_mock_state(x_offset=0):
    return GameState(
        timestamp=1234,
        tick=1.0,
        player={
            "status": "idle",
            "position": {"x": 100+x_offset, "y": 100, "z": 0},
            "rotation": 0,
            "state": {},
            "body": {"health": 100, "temperature": 37, "parts": {}},
            "moodles": {},
            "inventory": {"held": {}, "worn": [], "main": []},
            "vision": {
                "scan_radius": 10,
                "timestamp": 1234,
                "tiles": [
                    {"x": 100+x_offset, "y": 100, "z": 0},
                    {"x": 100+x_offset, "y": 101, "z": 0}
                ],
                "objects": [
                    {
                        "id": "zombie_1",
                        "type": "Zombie",
                        "x": 105+x_offset, "y": 100, "z": 0,
                        "meta": {}
                    }
                ],
                "neighbors": {}
            },
            "action_state": {"status": "idle", "sequence_number": -1, "queue_busy": False}
        }
    )

def test_world_model_persistence():
    model = WorldModel()
    
    # Step 1: Update with initial state
    print("Step 1: Feeding Frame 1 (x=100)...")
    state1 = create_mock_state(x_offset=0)
    model.update(state1)
    
    assert len(model.map.grid) == 2, f"Expected 2 tiles, got {len(model.map.grid)}"
    assert len(model.entities.entities) == 1, "Expected 1 zombie"
    assert model.entities.entities["zombie_1"].x == 105
    
    # Step 2: Update with new state (moved)
    print("Step 2: Feeding Frame 2 (x=101)...")
    state2 = create_mock_state(x_offset=1) # Tiles: 101, 102. Zombie: 106
    model.update(state2)
    
    # Verification:
    # 1. Tile 100 should still exist (persistence)
    tile_100 = model.map.get_tile(100, 100, 0)
    assert tile_100 is not None, "Tile 100,100 vanished!"
    assert tile_100.is_explored, "Tile 100,100 should be marked explored"
    
    # 2. Total tiles should be 4 (100,100; 100,101 from frame 1 + 101,100; 101,101 from frame 2)
    assert len(model.map.grid) == 4, f"Expected 4 unique tiles, got {len(model.map.grid)}"
    
    # 3. Zombie should be updated to new position
    zombie = model.entities.entities["zombie_1"]
    assert zombie.x == 106, f"Zombie did not move? x={zombie.x}"
    
    print("SUCCESS: WorldModel correctly aggregated vision data.")

if __name__ == "__main__":
    test_world_model_persistence()
