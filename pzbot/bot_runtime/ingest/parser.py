import json
import logging
from pathlib import Path
from bot_runtime.ingest.state import GameState

logger = logging.getLogger(__name__)

class StateParser:
    def __init__(self):
        pass

    def parse_file(self, file_path: Path) -> GameState:
        """Parses the game state from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self.parse_dict(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse state file {file_path}: {e}")
            raise

    def parse_dict(self, data: dict) -> GameState:
        """Parses the game state from a dictionary."""
        return GameState(**data)
