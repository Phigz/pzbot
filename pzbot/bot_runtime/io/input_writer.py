import uuid
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class Action(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    params: Dict[str, Any]

class ActionPacket(BaseModel):
    sequence_number: int
    id: str
    timestamp: int
    clear_queue: bool
    actions: List[Action]

class InputWriter:
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.current_sequence_number = 0
        
        # Try to resume sequence number if file exists
        if self.output_path.exists():
            try:
                with open(self.output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "sequence_number" in data:
                        self.current_sequence_number = data["sequence_number"]
                        logger.info(f"Resuming sequence from {self.current_sequence_number}")
            except Exception as e:
                logger.warning(f"Could not read existing sequence number: {e}")

    def write_actions(self, actions: List[Dict[str, Any]], clear_queue: bool = False, packet_id: Optional[str] = None):
        """
        Writes a list of actions to the input file.
        
        Args:
            actions: List of dicts, e.g. [{"type": "wait", "params": {"duration_ms": 1000}}]
            clear_queue: Whether to clear the existing action queue on the bot side.
            packet_id: Optional ID for the packet. Defaults to timestamp.
        """
        if packet_id is None:
            packet_id = f"cmd_{int(time.time() * 1000)}"

        self.current_sequence_number += 1
        
        # Ensure every action has an ID if not provided
        formatted_actions = []
        for a in actions:
            if "id" not in a:
                a["id"] = str(uuid.uuid4())
            formatted_actions.append(a)

        packet_data = {
            "sequence_number": self.current_sequence_number,
            "id": packet_id,
            "timestamp": int(time.time() * 1000),
            "clear_queue": clear_queue,
            "actions": formatted_actions
        }

        try:
            # Ensure parent exists
            if not self.output_path.parent.exists():
                logger.info(f"Creating missing directory: {self.output_path.parent}")
                self.output_path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write pattern: write to temp file then rename
            temp_path = self.output_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(packet_data, f, indent=4)
            
            # Retry logic for rename (Windows file locking)
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    temp_path.replace(self.output_path)
                    break # Success
                except OSError:
                    if attempt == max_retries - 1:
                        raise # Give up
                    time.sleep(0.01) # Wait 10ms
            
            logger.info(f"Wrote {len(actions)} actions to {self.output_path}")

        except Exception as e:
            logger.error(f"Failed to write input file {self.output_path}: {e}")
            raise
