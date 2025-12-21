import importlib
import pkgutil
import logging
from pathlib import Path

# Dynamic Scenario Loader
# Scans pzbot/tools/mock_bridge/tests/ for .py files and loads them.

logger = logging.getLogger("MockBridge")

SCENARIO_MAP = {}

def load_scenarios():
    """
    Dynamically loads scenarios from the 'pzbot.tools.mock_bridge.tests' package.
    Expects modules to have a function `run(world)`.
    """
    tests_package = "pzbot.tools.mock_bridge.tests"
    tests_dir = Path(__file__).parent / "tests"
    
    if not tests_dir.exists():
        logger.warning(f"Tests directory not found: {tests_dir}")
        return

    # Iterate over files in the tests directory
    for file_path in tests_dir.glob("*.py"):
        if file_path.name == "__init__.py":
            continue
            
        module_name = f"{tests_package}.{file_path.stem}"
        scenario_name = file_path.stem
        
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "run") and callable(module.run):
                SCENARIO_MAP[scenario_name] = module.run
                logger.debug(f"Registered scenario: {scenario_name}")
            else:
                logger.debug(f"Skipping {scenario_name}: No run() function found.")
        except Exception as e:
            logger.error(f"Failed to load scenario {scenario_name}: {e}")

# Load scenarios on import
load_scenarios()
