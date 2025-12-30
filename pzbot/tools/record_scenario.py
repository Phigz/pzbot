
import argparse
import gzip
import json
import logging
import time
import signal
import sys
import os
from pathlib import Path

# Ensure project root is in path
# Ensure project root is in path
sys.path.append(str(Path(__file__).parent.parent))

from bot_runtime.ingest.watcher import StateWatcher
from bot_runtime import config

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RECORDER")

class ScenarioRecorder:
    def __init__(self, name: str, output_dir: Path):
        self.name = name
        self.output_dir = output_dir
        self.output_path = output_dir / f"{name}.jsonl.gz"
        self.frame_count = 0
        self.start_time = 0.0
        self.is_recording = False
        self._file_handle = None

    def start(self):
        # Create directory if needed
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Open GZIP file in append mode (text mode via wt)
        self._file_handle = gzip.open(self.output_path, "wt", encoding="utf-8")
        
        self.is_recording = True
        self.start_time = time.time()
        logger.info(f"Started recording to: {self.output_path}")

    def on_tick(self, state_data: dict, raw_json: str = None):
        """
        Callback for StateWatcher. 
        We prefer raw_json if available to avoid re-serializing, but StateWatcher passes dict.
        """
        if not self.is_recording:
            return

        # Convert Pydantic model to dict if needed
        if hasattr(state_data, "model_dump"):
            state_data = state_data.model_dump()
        elif hasattr(state_data, "dict"):
            state_data = state_data.dict()

        frame = {
            "timestamp": time.time(),
            "tick_time": time.time() - self.start_time,
            "state": state_data
        }

        # Write as one line
        try:
            self._file_handle.write(json.dumps(frame) + "\n")
            self.frame_count += 1
            if self.frame_count % 100 == 0:
                # Flush occasionally to keep data safe
                self._file_handle.flush()
                print(f"\rRecorded {self.frame_count} frames...", end="")
        except Exception as e:
            logger.error(f"Failed to write frame: {e}")

    def stop(self):
        if self.is_recording:
            logger.info(f"\nStopping recording... Total Frames: {self.frame_count}")
            if self._file_handle:
                self._file_handle.close()
            self.is_recording = False

def main():
    parser = argparse.ArgumentParser(description="PZBot Scenario Recorder")
    parser.add_argument("--name", type=str, required=True, help="Name of the scenario recording")
    # Using the standard mock data directory for recordings by default
    parser.add_argument("--dir", type=str, default="data/recordings", help="Output directory for recordings")
    
    args = parser.parse_args()
    
    # Resolve paths
    base_dir = Path(__file__).parent.parent.parent
    output_dir = base_dir / args.dir
    
    recorder = ScenarioRecorder(args.name, output_dir)
    
    # Use Config's state file path (supports env vars)
    state_file = config.STATE_FILE_PATH
    logger.info(f"Watching state file at: {state_file}")

    # Initialize Watcher
    # Note: StateWatcher expects a callback that takes (state_dict)
    watcher = StateWatcher(
        state_file_path=state_file,
        on_update=recorder.on_tick,
        polling_interval=0.01 # Fast polling for high fidelity
    )

    # Handle graceful exit
    def signal_handler(sig, frame):
        watcher.stop()
        recorder.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        recorder.start()
        watcher.start()

        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Recorder crashed: {e}")
        recorder.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()
