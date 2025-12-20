# Implementation Plan: Mock Bridge Tests

## Goal
Establish a testing framework for the Mock Bridge to ensure it remains compliant with the PZ API schema and allows for visual verification of bot behavior.

## 1. Automated Unit Tests (`pzbot/tests/test_mock_compliance.py`)
To prevent brittleness as the schema evolves:
*   **Test**: `test_factory_output_schema_validity`
*   **Logic**:
    1.  Call `StateFactory.create_default_state()`.
    2.  Load `output_state.json` schema.
    3.  Assert `jsonschema.validate(instance, schema)` passes.
*   **Benefit**: If we add a required field to the schema and forget the factory, this test fails instantly.

## 2. Visual Test Scenarios
We will add a "Scenario" system to the Mock Bridge to simulate specific game situations for visual debugging.

### 2.1. Scenario Registry (`pzbot/tools/mock_bridge/scenarios.py`)
A simple registry of setup functions.
```python
def scenario_basic_zombies(world):
    world.set_player_pos(100, 100)
    world.add_zombie(105, 100, "z1") # Stationary zombie
    world.add_zombie(100, 105, "z2") # Stationary zombie
```

### 2.2. Integrate Scenarios into `main.py`
Add a `--scenario` CLI argument to `mock_bridge/main.py`.
*   If set, run the scenario setup function after initializing `MockWorld`.

## 3. Verification Plan

### 3.1. Automated Verification
Run `pytest pzbot/tests/test_mock_compliance.py`.

### 3.2. Manual Visual Verification
1.  Run Mock Bridge with Scenario:
    `python -m pzbot.tools.mock_bridge.main --scenario basic_zombies --dir ./data`
2.  (In separate tab) Run Bot Runtime:
    `python -m pzbot.bot_runtime.main` (configured to point to ./data)
3.  (In separate tab) Run Visualizer:
    `python -m pzbot.tools.visualize_grid`
4.  **Expectation**: The HTML map should show the player at 100,100 and two zombies at 105,100 and 100,105.
