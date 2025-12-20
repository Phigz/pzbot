import json
import logging
import time
from pathlib import Path
import jsonschema

logger = logging.getLogger(__name__)

class MockFileIO:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        
        # Paths
        self.state_path = base_dir / "state.json"
        self.input_path = base_dir / "input.json"
        
        # Load Schema
        # Assumes this file is in pzbot/tools/mock_bridge/file_io.py
        # And docs are in [ROOT]/docs/schemas/output_state.json
        # So we go up 3 levels to ROOT
        root_dir = Path(__file__).parent.resolve().parent.parent.parent
        schema_path = root_dir / "docs" / "schemas" / "output_state.json"
        
        if not schema_path.exists():
             # Fallback if we messed up structure, mostly for testing if moved
             logger.warning(f"Schema not found at {schema_path}, trying fallback resolution...")
             # Just fail if we can't find it strictly
             raise FileNotFoundError(f"Schema definition not found at {schema_path}")

        try:
            with open(schema_path, 'r') as f:
                self.output_schema = json.load(f)
            logger.info(f"Loaded Output Schema from {schema_path}")
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            raise e

    def write_state(self, state_data):
        """
        Validates and writes state to disk.
        """
        # 1. Validate
        try:
            jsonschema.validate(instance=state_data, schema=self.output_schema)
        except jsonschema.ValidationError as e:
            logger.error(f"FATAL: Generated Mock State failed validation: {e.message}")
            # We raise so tests fail loudly
            raise e
            
        # 2. Write
        tmp_path = self.state_path.with_suffix(".tmp")
        with open(tmp_path, 'w') as f:
            json.dump(state_data, f, indent=None) # Compact write for speed? Or indent for readability.
        
        # Atomic rename
        tmp_path.rename(self.state_path)

    def read_input(self):
        """
        Reads input.json if it exists.
        Returns command list or None.
        """
        if not self.input_path.exists():
            return None
            
        try:
            with open(self.input_path, 'r') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError:
            return None
        except Exception as e:
            logger.warning(f"Error reading input: {e}")
            return None
