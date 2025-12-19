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

    try:
        watcher.start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        watcher.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        watcher.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()
