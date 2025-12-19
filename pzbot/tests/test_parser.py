import sys
from pathlib import Path
import json

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from bot_runtime.ingest.parser import StateParser
from bot_runtime.ingest.state import GameState

def test_parser():
    parser = StateParser()
    state_file = Path("docs/example_state.json")
    
    if not state_file.exists():
        print(f"Error: {state_file} does not exist.")
        return

    try:
        state = parser.parse_file(state_file)
        print("Successfully parsed game state!")
        print(f"Timestamp: {state.timestamp}")
        print(f"Player Position: ({state.player.position.x}, {state.player.position.y}, {state.player.position.z})")
        print(f"Inventory Item Count (Main): {len(state.player.inventory.main)}")
        print(f"Visible Objects: {len(state.vision.objects)}")
    except Exception as e:
        print(f"Failed to parse: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parser()
