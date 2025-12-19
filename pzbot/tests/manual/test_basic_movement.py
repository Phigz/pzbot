import sys
import time
from pathlib import Path

# Add project root to path so we can import bot_runtime
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from bot_runtime.test_framework import TestSequencer

# CONFIG
INPUT_FILE = Path("c:/Users/lucas/Zomboid/Lua/AISurvivorBridge/input.json")

def main():
    print(f"Initializing TestSequencer pointing to: {INPUT_FILE}")
    seq = TestSequencer(INPUT_FILE)

    print("Building sequence...")
    # 1. Wait a bit
    # 2. Look somewhere
    # 3. Walk somewhere nearby (Assuming typical Muldraugh spawn coordinates around 10800, 10060)
    #    Adjust these coordinates if your bot is elsewhere!
    
    seq.wait(1000) \
       .look_to(10810, 10070) \
       .toggle_crouch(True) \
       .wait(1000) \
       .move_to(10800, 10070, running=False) \
       .toggle_crouch(False) \
       .sit()

    print("Sending sequence...")
    seq.execute(clear_queue=True, description="manual_movement_test_01")
    print("Done. Check game.")

if __name__ == "__main__":
    main()
