import sys
from pathlib import Path
import json

# Setup path to import bot_runtime
sys.path.append(str(Path(__file__).parent.parent))

from bot_runtime.ingest.state import GameState, Player, ActionState

def test_state_parsing():
    print("Testing State Parsing...")
    
    # Mock JSON matching existing schema + new ActionState
    # Minimal fields required by models
    mock_data = {
        "timestamp": 1234567890,
        "tick": 12.34,
        "player": {
            "status": "idle",
            "position": {"x":0,"y":0,"z":0},
            "rotation": 0.0,
            "state": {},
            "body": {
                "health": 100,
                "parts": {}
            },
            "inventory": {},
            "vision": {},
            "action_state": {
                "status": "executing",
                "sequence_number": 5,
                "queue_busy": True,
                "current_action_id": "uuid-123",
                "current_action_type": "move_to"
            }
        }
    }

    try:
        gs = GameState(**mock_data)
        print("Parsing Successful!")
        
        # Verify fields
        assert gs.player.action_state.sequence_number == 5
        assert gs.player.action_state.current_action_id == "uuid-123"
        assert gs.player.action_state.queue_busy is True
        print("Field Verification Passed!")
        
    except Exception as e:
        print(f"Parsing Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_state_parsing()
