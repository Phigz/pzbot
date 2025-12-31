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
    for p in [snapshot_path, config.STATE_FILE_PATH]:
        if p.exists():
            try:
                p.unlink()
                logger.info(f"Cleaned up previous data at {p}")
            except Exception as e:
                logger.warning(f"Failed to clean up {p}: {e}")

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
                known_zombies = [flatten_entity(e) for e in world_model.memory.get_zombies()]
                vehicles = [flatten_entity(e) for e in world_model.memory.get_known_vehicles()]
                
                grid_data = {
                    "zombies": known_zombies,
                    "nearby_containers": n_containers,
                    "world_items": w_items,
                    "vehicles": vehicles
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
