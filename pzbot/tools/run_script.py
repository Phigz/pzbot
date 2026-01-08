import time
import sys
import yaml
import logging
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from bot_runtime import config
from bot_runtime.logging_setup import setup_logging
from bot_runtime.io.input_writer import InputWriter
from bot_runtime.input.service import InputService
from bot_runtime.ingest.watcher import StateWatcher
from bot_runtime.ingest.state import GameState

logger = logging.getLogger(__name__)

class ScriptRunner:
    def __init__(self, script_path: Path):
        self.script_path = script_path
        self.input_writer = InputWriter(output_path=config.INPUT_FILE_PATH)
        self.input_service = InputService.get_provider()
        self.state = None
        self.running = True
        
    def on_state_update(self, state: GameState):
        self.state = state
        
    def run(self):
        logger.info(f"Loading script from {self.script_path}")
        with open(self.script_path, 'r') as f:
            script_data = yaml.safe_load(f)
            
        steps = script_data.get('steps', [])
        logger.info(f"Script loaded with {len(steps)} steps.")
        
        # Start Watcher for state awareness (safety checks)
        watcher = StateWatcher(config.STATE_FILE_PATH, self.on_state_update)
        watcher.start()
        
        t0 = time.time()
        
        try:
            for i, step in enumerate(steps):
                step_name = step.get('name', f'Step {i}')
                action_type = step.get('type', 'Wait')
                params = step.get('params', {})
                duration = step.get('duration', 0)
                
                logger.info(f"Executing: {step_name} [{action_type}]")
                
                # Wait for safety
                while self.state and not self.input_service.check_safety(self.state):
                    logger.warning("Input blocked by Safety Gate. Waiting...")
                    time.sleep(1.0)
                
                if action_type == 'Wait':
                    time.sleep(duration)
                    
                elif action_type == 'Walk':
                    # Emulate Direct Movement
                    direction = params.get('direction', 'w')
                    # We hold chunks of 0.1s to allow safety checks?
                    # Or just hold for duration.
                    self.input_service.hold(direction, duration)
                    
                elif action_type == 'LuaAction':
                    # Send to input.json
                    lua_action = {
                        "type": params.get('action_type'),
                        "params": params.get('data', {})
                    }
                    self.input_writer.write_actions([lua_action])
                    if duration > 0:
                        time.sleep(duration)
                        
                elif action_type == 'LookAt':
                     lua_action = { "type": "FaceLocation", "params": params }
                     self.input_writer.write_actions([lua_action])
                     time.sleep(0.5) # Wait for turn
                
                else:
                    logger.warning(f"Unknown action type: {action_type}")
                    
        except KeyboardInterrupt:
            logger.info("Script interrupted.")
        finally:
            watcher.stop()
            logger.info("Script finished.")

if __name__ == "__main__":
    setup_logging()
    parser = argparse.ArgumentParser(description="Run a bot script.")
    parser.add_argument("script", help="Path to YAML script file")
    args = parser.parse_args()
    
    runner = ScriptRunner(Path(args.script))
    runner.run()
