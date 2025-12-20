import pytest
import json
import jsonschema
from pathlib import Path
from pzbot.tools.mock_bridge.state_factory import StateFactory

def test_factory_output_schema_validity():
    """
    Ensures that the default state produced by the factory complies with 
    the project's official output_state.json schema.
    """
    # 1. Generate State
    data = StateFactory.create_default_state()
    
    # 2. Load Schema
    # Navigate: tests/ -> mock_bridge/ -> tools/ -> pzbot/ -> [ROOT]/ -> docs/schemas/output_state.json
    root_dir = Path(__file__).parent.parent.parent.parent.parent
    schema_path = root_dir / "docs" / "schemas" / "output_state.json"
    
    assert schema_path.exists(), f"Schema file not found at {schema_path}"
    
    with open(schema_path, 'r') as f:
        schema = json.load(f)
        
    # 3. Validate
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"StateFactory output failed schema validation: {e.message}")
