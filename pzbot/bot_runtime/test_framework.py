import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from .io.input_writer import InputWriter

logger = logging.getLogger(__name__)

class TestSequencer:
    """
    A fluent API for constructing and sending command batches to the bot.
    Useful for integration tests and manual verification scripts.
    """
    def __init__(self, input_path: Path):
        self.writer = InputWriter(input_path)
        self.current_batch: List[Dict[str, Any]] = []

    def wait(self, duration_ms: int) -> 'TestSequencer':
        """Adds a wait command."""
        self.current_batch.append({
            "type": "wait",
            "params": {"duration_ms": duration_ms}
        })
        return self

    def move_to(self, x: float, y: float, z: float = 0, running: bool = False, sprinting: bool = False) -> 'TestSequencer':
        """Adds a move_to command."""
        self.current_batch.append({
            "type": "move_to",
            "params": {
                "x": x, 
                "y": y, 
                "z": z,
                "running": running,
                "sprinting": sprinting
            }
        })
        return self

    def look_to(self, x: float, y: float) -> 'TestSequencer':
        """Adds a look_to command."""
        self.current_batch.append({
            "type": "look_to",
            "params": {"x": x, "y": y}
        })
        return self

    def sit(self) -> 'TestSequencer':
        """Adds a sit command."""
        self.current_batch.append({
            "type": "sit",
            "params": {}
        })
        return self

    def toggle_crouch(self, active: bool) -> 'TestSequencer':
        """Adds a toggle_crouch command."""
        self.current_batch.append({
            "type": "toggle_crouch",
            "params": {"active": active}
        })
        return self

    def add_custom(self, action_type: str, params: Dict[str, Any]) -> 'TestSequencer':
        """Adds a custom raw command."""
        self.current_batch.append({
            "type": action_type,
            "params": params
        })
        return self

    def execute(self, clear_queue: bool = True, description: Optional[str] = None):
        """
        Writes the current batch to the input file.
        
        Args:
            clear_queue: If None (default), uses the default behavior (likely True). 
                         Actually InputWriter expects bool, defaulting to False if strict.
                         Here we default to True for test sequences to ensure they run immediately.
            description: Optional ID/String for logging.
        """
        if not self.current_batch:
            logger.warning("Execute called with empty batch.")
            return

        batch_id = description or f"test_seq_{int(time.time())}"
        logger.info(f"Executing Test Batch '{batch_id}' ({len(self.current_batch)} actions)...")
        
        self.writer.write_actions(
            actions=self.current_batch,
            clear_queue=clear_queue,
            packet_id=batch_id
        )
        
        # Clear local batch after sending
        self.current_batch = []
