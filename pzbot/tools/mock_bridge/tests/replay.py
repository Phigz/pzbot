
import gzip
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("REPLAY")

def run(world):
    """
    Simulates a replay by reading from a recording file.
    The recording file path is expected to be passed via a global variable or config 
    since the function signature is fixed.
    
    However, for a clean implementation within the current architecture, 
    we need to check for the 'replay_file' attribute on the world object or similar injection.
    """
    
    # We will patch this in main.py to inject the path
    recording_path = getattr(world, 'replay_file', None)
    
    if not recording_path:
        logger.error("No replay file specified! Use --replay <path> in main.py")
        return

    path = Path(recording_path)
    if not path.exists():
        logger.error(f"Replay file not found: {path}")
        return

    logger.info(f"Starting Replay from: {path}")
    
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    frame = json.loads(line)
                    state_data = frame.get("state")
                    timestamp = frame.get("timestamp", 0)
                    
                    if state_data:
                        # Direct state injection
                        world.state = state_data
                        
                        # Yield to let the main loop define the speed
                        # In the future we can use frame['timestamp'] to respect real timing
                        yield
                        
                except json.JSONDecodeError:
                    continue
                    
    except Exception as e:
        logger.error(f"Replay failed: {e}")
        
    logger.info("Replay finished.")
