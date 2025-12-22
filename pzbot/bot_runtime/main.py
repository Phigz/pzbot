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
                # Extract Persistent Resource Data from EntityManager
                def transform_entities(entities):
                    res = []
                    for e in entities:
                        # Base fields
                        d = e.model_dump(exclude={'properties'})
                        # Merge properties (flatten)
                        if e.properties:
                            d.update(e.properties)
                        res.append(d)
                    return res

                w_items = transform_entities(world_model.entities.get_known_items())
                n_containers = transform_entities(world_model.entities.get_known_containers())
                
                world_model.grid.save_snapshot(str(snapshot_path), world_items=w_items, nearby_containers=n_containers)
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
