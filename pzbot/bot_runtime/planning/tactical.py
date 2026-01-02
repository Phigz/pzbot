import logging
from bot_runtime.world.model import WorldModel
from bot_runtime.control.builders.wait import WaitExecutor
from bot_runtime.control.builders.movement import MovementExecutor

logger = logging.getLogger(__name__)

class TacticalPlanner:
    def __init__(self, world_model: WorldModel, wait_executor: WaitExecutor, moving_executor: MovementExecutor):
        self.world_model = world_model
        self.wait_exec = wait_executor
        self.move_exec = moving_executor

    def update(self):
        """
        Decide on immediate actions based on world model.
        """
        # Example logic:
        # If player is idle (not doing anything), wait for a bit.
        # Real logic would check threats, hunger, etc.
        
        player = self.world_model.player
        if player and player.status == "idle":
             # Just an example behavior
            pass
