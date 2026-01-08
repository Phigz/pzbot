from abc import ABC, abstractmethod
from typing import Dict, Any, Generator, Optional
from pathlib import Path
import json
import gzip
import logging

class RecordingProcessor(ABC):
    """
    Base class for all Dream Engine processors.
    A processor takes a .jsonl.gz recording and outputs a result dict (config/weights).
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def name(self) -> str:
        """Unique name for this processor (e.g., 'tactical_heatmap')"""
        pass

    @abstractmethod
    def process(self, recording_path: Path) -> Optional[Dict[str, Any]]:
        """
        Process a single recording file.
        Returns a dictionary of results to be aggregated, or None if skipped.
        """
        pass

    def stream_frames(self, recording_path: Path) -> Generator[Dict[str, Any], None, None]:
        """Helper to safely stream frames from a recording."""
        if not recording_path.exists():
            self.logger.error(f"Recording not found: {recording_path}")
            return
            
        # Helper for delta application
        # Since this runs in a separate process, we might need to duplicate apply_delta or import it
        # Let's import it safely
        try:
             from tools.delta_util import apply_delta
        except ImportError:
             from pzbot.tools.delta_util import apply_delta

        last_full_state = {}

        try:
            with gzip.open(recording_path, 'rt', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        data = json.loads(line)
                        
                        # Handle new format (Keyframe/Delta)
                        # New format wraps content in 'k', 'd', 'ts'
                        if "k" in data:
                            is_key = data.get("k", False)
                            
                            if is_key:
                                # Keyframe: Update baseline and yield
                                # We need to extract the actual state data.
                                # In recorder I did: payload = data (the full state) -> final_obj.update(payload)
                                # So the state keys are mixed with 'k', 'ts', 'f'.
                                # We should strip metadata before yielding if we want purity?
                                # Or just yield as is. 
                                # Processors expect 'player', 'tick', etc.
                                last_full_state = data
                                yield data
                            else:
                                # Delta: Apply diff to last_full_state
                                delta = data.get("d", {})
                                reconstructed = apply_delta(last_full_state, delta)
                                
                                # Update timestamp/frame index from current packet
                                reconstructed["ts"] = data.get("ts")
                                reconstructed["f"] = data.get("f")
                                reconstructed["k"] = False
                                
                                # Update our running state (P-Frame style check: recorder diffs against last full state? 
                                # Wait, recorder: self.last_full_state = data (the CURRENT full state).
                                # So yes, we maintain the full state in sync.)
                                last_full_state = reconstructed
                                yield reconstructed
                                
                        else:
                            # Legacy format (raw state dump)
                            yield data
                            
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.logger.error(f"Error reading {recording_path}: {e}")

    def save_artifact(self, data: Any, filename: str, output_dir: Path):
        """Helper to save processor output to the config directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / filename
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Saved artifact: {path}")
        except Exception as e:
            self.logger.error(f"Failed to save artifact {path}: {e}")
