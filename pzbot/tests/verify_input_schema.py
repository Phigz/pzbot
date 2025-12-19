import sys
from pathlib import Path
import json
import shutil

# Setup path to import bot_runtime
sys.path.append(str(Path(__file__).parent.parent))

from bot_runtime.io.input_writer import InputWriter

def test_input_schema():
    print("Testing Input Schema...")
    test_path = Path("test_input.json")
    writer = InputWriter(test_path)

    # Test Batch 1
    actions_1 = [{"type": "wait", "params": {"duration": 100}}]
    writer.write_actions(actions_1)

    with open(test_path, "r") as f:
        data = json.load(f)
        
    assert "sequence_number" in data, "Missing sequence_number"
    assert data["sequence_number"] == 1, f"Expected seq 1, got {data['sequence_number']}"
    assert "actions" in data, "Missing actions"
    assert len(data["actions"]) == 1
    assert "id" in data["actions"][0], "Action missing ID"
    print("Batch 1 Passed")

    # Test Batch 2 (Sequence Increment)
    actions_2 = [{"type": "move_to", "params": {"x": 10, "y": 20}}]
    writer.write_actions(actions_2)

    with open(test_path, "r") as f:
        data = json.load(f)
        
    assert data["sequence_number"] == 2, f"Expected seq 2, got {data['sequence_number']}"
    print("Batch 2 Passed")

    # Cleanup
    if test_path.exists():
        test_path.unlink()
    print("All Tests Passed!")

if __name__ == "__main__":
    test_input_schema()
