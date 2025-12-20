import sys
import time
import argparse
import logging
from pathlib import Path

# Fix path to include pzbot package if run directly
sys.path.append(str(Path(__file__).parent.parent.parent))

from pzbot.tools.mock_bridge.world_sim import MockWorld
from pzbot.tools.mock_bridge.file_io import MockFileIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [MOCK] - %(message)s')
logger = logging.getLogger("MockBridge")

def main():
    parser = argparse.ArgumentParser(description="Mock Project Zomboid Lua Bridge")
    parser.add_argument("--dir", type=str, default=".", help="Directory to write state.json/read input.json")
    parser.add_argument("--fps", type=int, default=10, help="Target ticks per second")
    parser.add_argument("--scenario", type=str, choices=["empty", "basic", "surrounded"], default="empty", help="Load a pre-set scenario")
    args = parser.parse_args()

    data_dir = Path(args.dir).resolve()
    logger.info(f"Starting Mock Bridge in {data_dir} with scenario '{args.scenario}'")
    
    # Initialize implementation
    try:
        io = MockFileIO(data_dir)
        sim = MockWorld()
        
        # Load Scenario
        from pzbot.tools.mock_bridge.scenarios import SCENARIO_MAP
        if args.scenario in SCENARIO_MAP:
             SCENARIO_MAP[args.scenario](sim)
             logger.info(f"Loaded scenario: {args.scenario}")
             
    except Exception as e:
        logger.error(f"Initialization Failed: {e}")
        sys.exit(1)

    target_dt = 1.0 / args.fps
    
    try:
        while True:
            start_time = time.time()
            
            # 1. Read Input (Stubbed for now as requested)
            commands = io.read_input()
            if commands:
                # In future: sim.apply_commands(commands)
                logger.debug(f"Received input batch: {commands.get('id', 'unknown')}")
                pass
            
            # 2. Update Sim
            sim.update(target_dt)
            
            # 3. Write State
            snapshot = sim.get_state_snapshot()
            io.write_state(snapshot)
            
            # 4. Sleep
            elapsed = time.time() - start_time
            sleep_time = max(0, target_dt - elapsed)
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logger.info("Stopping Mock Bridge...")

if __name__ == "__main__":
    main()
