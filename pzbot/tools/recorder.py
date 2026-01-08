import sys
import time
import json
import gzip
import shutil
import threading
import logging
from pathlib import Path
from datetime import datetime

# Setup paths - Assume we are in tools/recorder.py or similar
# We need to find the root pzbot directory
CURRENT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = CURRENT_DIR.parent
CONFIG_DIR = ROOT_DIR / "config"
LOGS_DIR = ROOT_DIR / "logs"
RECORDINGS_DIR = ROOT_DIR / "scenarios" / "recordings"

# Ensure dirs exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
# Ensure we can import tools
sys.path.append(str(ROOT_DIR))

try:
    from tools.delta_util import compute_delta
except ImportError:
    # If ran from root
    from pzbot.tools.delta_util import compute_delta

# State File Path (Hardcoded or could read from config)
# Usually at Lua/AISurvivorBridge/state.json, but depends on user setup. 
# We'll try to find it relative to current script or use a default.
# The user env says: c:\Users\lucas\Zomboid\Lua\AISurvivorBridge\state.json
# BUT standard pzbot structure expects it elsewhere? 
# Let's check config.py if we can, or just look for the known location.
# In `main.py` it uses `config.STATE_FILE_PATH`.
# Let's try to import config.
sys.path.append(str(ROOT_DIR))
try:
    from bot_runtime import config
    STATE_FILE_PATH = config.STATE_FILE_PATH
except ImportError:
    print("Could not import bot_runtime.config. Using default path.")
    STATE_FILE_PATH = Path(r"C:\Users\lucas\Zomboid\Lua\AISurvivorBridge\state.json")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "recorder.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Recorder")

class Recorder:
    def __init__(self, state_path: Path, output_dir: Path, lite_mode: bool = False):
        self.state_path = state_path
        self.output_dir = output_dir
        self.lite_mode = lite_mode
        self.running = False
        self.paused = False
        
        self.frame_count = 0
        self.keyframe_interval = 60 # Full save every ~12s at 5Hz
        self.last_full_state = None
        
        self.start_time = 0
        self._last_mtime = 0
        
        # Output handles
        self.out_file = None
        self.gzip_file = None
        
        # Bookmark counter
        self.bookmarks = 0

    def start(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gameplay_{timestamp}.jsonl.gz"
        file_path = self.output_dir / filename
        
        logger.info(f"Starting recording to {file_path}")
        logger.info(f"Watching state file: {self.state_path}")
        
        try:
            self.out_file = open(file_path, "wb") # Gzip expects binary
            self.gzip_file = gzip.GzipFile(fileobj=self.out_file, mode="wb")
            
            self.running = True
            self.start_time = time.time()
            
            # Start Input Thread
            input_thread = threading.Thread(target=self._input_loop, daemon=True)
            input_thread.start()
            
            self._record_loop()
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
        finally:
            self.stop()

    def stop(self):
        if not self.running: return
        
        self.running = False
        logger.info("Stopping recording...")
        
        if self.gzip_file:
            self.gzip_file.close()
        if self.out_file:
            self.out_file.close()
            
        elapsed = time.time() - self.start_time
        logger.info(f"Recording saved. Frames: {self.frame_count}. Time: {elapsed:.1f}s.")

    def add_bookmark(self, label="bookmark"):
        """Injects a metadata frame into the stream"""
        self.bookmarks += 1
        meta_frame = {
            "meta_type": "bookmark",
            "id": self.bookmarks,
            "label": label,
            "timestamp": time.time(),
            "frame_index": self.frame_count
        }
        self._write_frame(meta_frame)
        logger.info(f"Bookmark #{self.bookmarks} added [{label}]")

    def _write_frame(self, data: dict):
        # Lite Mode Filtering
        if self.lite_mode:
            try:
                if "player" in data and "vision" in data["player"]:
                    if "tiles" in data["player"]["vision"]:
                        del data["player"]["vision"]["tiles"]
            except Exception:
                pass
        
        # Delta Compression Logic
        # Frame 0 is always Keyframe.
        # Every N frames is Keyframe.
        is_keyframe = (self.frame_count % self.keyframe_interval == 0) or (self.last_full_state is None)
        
        payload = {}
        
        if is_keyframe:
            payload = data
            self.last_full_state = data
            # Mark it implicitly as keyframe by structure? 
            # Or add a meta field. 
            # Let's add meta field to help parser.
            # But wait, we want 'data' to be pure state for easy reading?
            # Let's wrap it: {"t": time, "type": "K", "data": ...}
            # Actually, to keep it compatible with simple JSONL readers, let's keep root structure mostly 
            # but maybe add a top level key.
            # Compatibility Strategy:
            # If line has "tick", it's a frame.
            # If is_keyframe, it looks normal.
            # If delta, it has "delta": True
        else:
            diff = compute_delta(self.last_full_state, data)
            if diff is None: 
                 # No change, skip writing frame entirely? 
                 # No, we want time continuity. Write empty delta.
                 diff = {}
                 
            payload = {"delta": True, "d": diff}
            # Update prediction of state for next diff? 
            # No, 'compute_delta' works best if diffing against LAST KEYFRAME or LAST STATE?
            # Standard video encoding diffs against Last Frame ("P-Frame").
            # Let's diff against Last Frame (P-Frame style) to keep deltas smallest.
            self.last_full_state = data

        # Add timestamp wrapper to everything
        final_obj = {
            "ts": time.time(),
            "f": self.frame_count,
            "k": is_keyframe 
        }
        final_obj.update(payload)
        
        # Serialize to JSON line
        line = json.dumps(final_obj) + "\n"
        self.gzip_file.write(line.encode('utf-8'))
        self.frame_count += 1

    def _record_loop(self):
        print("Recorder Running. Controls:")
        print("  [ENTER] - Add Bookmark")
        print("  'q' + [ENTER] - Stop & Save")
        
        while self.running:
            try:
                if self.state_path.exists():
                    stat = self.state_path.stat()
                    mtime = stat.st_mtime
                    
                    if mtime > self._last_mtime:
                        self._last_mtime = mtime
                        
                        # Read Code
                        # We use a retry loop because file might be locked by Lua writing
                        for _ in range(3):
                            try:
                                with open(self.state_path, "r", encoding='utf-8') as f:
                                    content = f.read()
                                    if not content: continue
                                    
                                    data = json.loads(content)
                                    self._write_frame(data)
                                    
                                    # Optional: print status inline every 100 frames
                                    if self.frame_count % 50 == 0:
                                        sys.stdout.write(f"\rFrames: {self.frame_count} | Bookmarks: {self.bookmarks}")
                                        sys.stdout.flush()
                                    break
                            except json.JSONDecodeError:
                                # Partial write, skip
                                time.sleep(0.01)
                            except Exception as e:
                                logger.warning(f"Read error: {e}")
                                time.sleep(0.01)
                                
                else:
                    # Waiting for file or Game Paused
                    pass

                # UI Update for Pause State
                if self.running and (time.time() - self._last_mtime > 5.0) and self.frame_count > 0:
                     sys.stdout.write(f"\r[Status: Paused/Waiting] Frames: {self.frame_count} | Bookmarks: {self.bookmarks}   ")
                     sys.stdout.flush()
                
                time.sleep(0.01) # fast poll
                
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                logger.error(f"Loop error: {e}")
                time.sleep(1)

    def _input_loop(self):
        """Thread to handle console input for bookmarks"""
        while self.running:
            try:
                txt = input()
                if txt.strip().lower() == 'q':
                    logger.info("Quit command received.")
                    self.stop()
                    # We need to break the main loop too, handled by self.running check or OS signal
                    # Since main loop runs in main thread, setting self.running closes it eventually
                    break
                else:
                    label = txt.strip() if txt.strip() else "User Marker"
                    self.add_bookmark(label)
                    print(f"Bookmark Added: {label}")
            except EOFError:
                break

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PZBot Gameplay Recorder")
    parser.add_argument("--state", type=Path, default=STATE_FILE_PATH, help="Path to state.json to watch")
    parser.add_argument("--output", type=Path, default=RECORDINGS_DIR, help="Directory to save recordings")
    parser.add_argument("--lite", action="store_true", help="Strip static tile data to save space (Recommended)")
    
    args = parser.parse_args()
    
    if not args.state.exists():
        logger.warning(f"State file not found at {args.state}. Ensure the game is running or will start soon.")
    
    rec = Recorder(args.state, args.output, lite_mode=args.lite)
    rec.start()
