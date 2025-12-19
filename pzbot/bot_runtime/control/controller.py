import logging
from typing import Optional
from bot_runtime.ingest.state import GameState
from bot_runtime.world.model import WorldModel
from bot_runtime.control.action_queue import ActionQueue
from bot_runtime.io.input_writer import InputWriter
from bot_runtime.world.logger import WorldLogger

logger = logging.getLogger(__name__)

class BotController:
    def __init__(self, world_model: WorldModel, action_queue: ActionQueue, input_writer: InputWriter):
        self.world_model = world_model
        self.action_queue = action_queue
        self.input_writer = input_writer
        
        self.world_logger = WorldLogger(self.world_model)

    def on_tick(self, game_state: GameState):
        """Called whenever a new game state is received."""
        # 1. Update World Model
        self.world_model.update(game_state)

        # 2. Log World Status
        self.world_logger.update()
        
        # 3. Flush Action Queue to Input Writer
        # DISABLED for World Model building phase - Pure Observer Mode
        # if self.action_queue.has_actions():
        #     actions = self.action_queue.pop_all()
        #     logger.info(f"Flushing {len(actions)} actions.")
        #     self.input_writer.write_actions(actions)
