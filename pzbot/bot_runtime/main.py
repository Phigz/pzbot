import time
import logging
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.append(str(Path(__file__).parent.parent))

from bot_runtime import config
from bot_runtime.logging_setup import setup_logging
from bot_runtime.ingest.watcher import StateWatcher
from bot_runtime.world.model import WorldModel
from bot_runtime.control.action_queue import ActionQueue
from bot_runtime.control.controller import BotController
from bot_runtime.io.input_writer import InputWriter

logger = logging.getLogger(__name__)

def main():
    setup_logging()
    logger.info("Starting Bot Runtime...")

    # Initialize components
    world_model = WorldModel()
    action_queue = ActionQueue()
    input_writer = InputWriter(output_path=config.INPUT_FILE_PATH)
    # Clear any stale inputs
    input_writer.write_actions([], clear_queue=True, packet_id="init_clear")
    controller = BotController(world_model, action_queue, input_writer)

    # Initialize Watcher
    watcher = StateWatcher(
        state_file_path=config.STATE_FILE_PATH,
        on_update=controller.on_tick,
        polling_interval=config.POLLING_INTERVAL
    )

    # Snapshot settings
    last_snapshot_time = 0.0
    SNAPSHOT_INTERVAL = 0.5 # seconds
    snapshot_path = config.BASE_DIR / "tools" / "grid_snapshot.json"

    # Cleanup previous runtime data
    # Logic: If state.json is 'fresh' (modified < 5s ago), assume game is running and don't delete it.
    # This allows 'Hot Attach' of the bot.
    if snapshot_path.exists():
        try:
            snapshot_path.unlink()
            logger.info(f"Cleaned up previous data at {snapshot_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up {snapshot_path}: {e}")

    state_path = config.STATE_FILE_PATH
    if state_path.exists():
        try:
            mtime = state_path.stat().st_mtime
            age = time.time() - mtime
            if age < 5.0:
                logger.info(f"State file is fresh ({age:.1f}s old). Assuming Hot Attach - preserving file.")
            else:
                state_path.unlink()
                logger.info(f"Cleaned up stale state file at {state_path}")
        except Exception as e:
            logger.warning(f"Failed to check/cleanup {state_path}: {e}")

    try:
        watcher.start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
            # Periodic Snapshot
            if time.time() - last_snapshot_time > SNAPSHOT_INTERVAL:
                # Extract Persistent Resource Data
                # Note: MemorySystem getters return list of dicts with properties embedded
                # We assume debug_bot can handle this or that returned dicts are compliant
                # The returned dict (EntityData.dict) has properties nested in 'properties'
                # but input to snapshot expects top-level fields for some tools? 
                
                # Let's write a small helper to flatten properties for compatibility
                def flatten_entity(entity_dict):
                    props = entity_dict.pop('properties', {}) or {}
                    # Prioritize concrete fields in entity_dict over props
                    # So update props with entity_dict, then return props
                    # Wait, we want dict -> props -> result. 
                    # dict has id, type, x, y, z. props has extra.
                    res = props.copy()
                    res.update(entity_dict)
                    return res

                w_items = [flatten_entity(e) for e in world_model.memory.get_known_items()]
                n_containers = [flatten_entity(e) for e in world_model.memory.get_known_containers()]
                known_entities = [flatten_entity(e) for e in world_model.memory.get_entities()]
                vehicles = [flatten_entity(e) for e in world_model.memory.get_known_vehicles()]
                signals = world_model.memory.get_signals()
                sounds = world_model.memory.get_sounds()
                
                # Brain State
                import dataclasses
                brain_data = dataclasses.asdict(controller.brain.state)
                # Exclude 'vision' as it contains non-serializable Pydantic objects and is too large
                if 'vision' in brain_data:
                    del brain_data['vision']
                if 'player' in brain_data:
                    del brain_data['player']
                
                grid_data = {
                    "entities": known_entities,
                    "nearby_containers": n_containers,
                    "world_items": w_items,
                    "vehicles": vehicles,
                    "signals": signals,
                    "sounds": sounds,
                    "brain": brain_data
                }
                
                world_model.grid.save_snapshot(str(snapshot_path), grid_data)
                last_snapshot_time = time.time()

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        world_model.grid.save_snapshot(str(snapshot_path))
        watcher.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        watcher.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()
