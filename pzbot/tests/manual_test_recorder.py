import sys
import time
import json
import gzip
import shutil
import threading
import subprocess
from pathlib import Path

# Setup paths
CURRENT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = CURRENT_DIR.parent
sys.path.append(str(ROOT_DIR))

RECORDER_SCRIPT = ROOT_DIR / "tools" / "recorder.py"
TEMP_DIR = ROOT_DIR / "tests" / "temp_recorder_test"
STATE_FILE = TEMP_DIR / "state.json"
OUTPUT_DIR = TEMP_DIR / "recordings"

def setup_env():
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True)
    OUTPUT_DIR.mkdir(parents=True)
    
    # Create initial state
    with open(STATE_FILE, 'w') as f:
        json.dump({"tick": 0, "status": "init"}, f)

def run_test():
    setup_env()
    print("Environment setup.")
    
    # Start Recorder
    cmd = [sys.executable, str(RECORDER_SCRIPT), "--state", str(STATE_FILE), "--output", str(OUTPUT_DIR)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True) # text=True for input
    
    print("Recorder started.")
    time.sleep(2) # Wait for init
    
    # Simulate updates
    for i in range(1, 6):
        data = {"tick": i, "player": {"x": i, "y": 0, "z": 0}}
        
        # Write to state file
        with open(STATE_FILE, 'w') as f:
            json.dump(data, f)
            
        print(f"Update {i} written.")
        time.sleep(0.5)
        
    # Send bookmark
    print("Sending bookmark command...")
    try:
        proc.stdin.write("Bookmark Test\n")
        proc.stdin.flush()
    except Exception as e:
        print(f"Failed to write to stdin: {e}")

    time.sleep(1)
    
    # Stop Recorder
    print("Stopping recorder...")
    try:
        proc.stdin.write("q\n")
        proc.stdin.flush()
    except Exception as e:
        print(f"Failed to write quit command: {e}")
        
    proc.wait(timeout=5)
    
    # Verify Output
    files = list(OUTPUT_DIR.glob("*.jsonl.gz"))
    if not files:
        print("FAIL: No recording file found.")
        sys.exit(1)
        
    rec_file = files[0]
    print(f"Checking {rec_file}...")
    
    # Use RecordingProcessor to reconstruct frames
    # This verifies the entire stack (Writer -> Reader)
    from tools.dream.lib.processor import RecordingProcessor
    
    # Mock processor to access stream_frames
    class MockProc(RecordingProcessor):
        def name(self): return "mock"
        def process(self, p): return {}
        
    proc = MockProc()
    lines = list(proc.stream_frames(rec_file))
            
    print(f"found {len(lines)} frames.")
    
    # Check content
    ticks = [l.get('tick') for l in lines if 'tick' in l]
    print(f"Recorded ticks: {ticks}")
    
    bookmarks = [l for l in lines if l.get('meta_type') == 'bookmark']
    print(f"Found {len(bookmarks)} bookmarks.")
    
    if len(ticks) >= 5 and len(bookmarks) >= 1:
        print("SUCCESS: Recorder works as expected.")
    else:
        print("FAIL: Missing data.")
        sys.exit(1)
        
    # Cleanup
    shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    run_test()
