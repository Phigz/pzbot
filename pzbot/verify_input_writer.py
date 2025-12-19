from pathlib import Path
from bot_runtime.io.input_writer import InputWriter

# Point to the file we know exists and has 9999
target_path = Path("C:/Users/lucas/Zomboid/Lua/AISurvivorBridge/input.json")
try:
    writer = InputWriter(target_path)
    print(f"writer.current_sequence_number = {writer.current_sequence_number}")
    if writer.current_sequence_number == 9999:
        print("SUCCESS: Picked up 9999")
    else:
        print(f"FAILURE: Expected 9999, got {writer.current_sequence_number}")
except Exception as e:
    print(f"ERROR: {e}")
