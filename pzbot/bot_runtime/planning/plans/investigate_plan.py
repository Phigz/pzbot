from typing import List
from bot_runtime.brain.state import BrainState
from bot_runtime.control.action_queue import Action, ActionType
from bot_runtime.planning.base import Plan, PlanStatus
import math

class InvestigatePlan(Plan):
    """
    Simple FSM to walk to a location/container to inspect it.
    Use case: "I see a crate but don't know what's inside" or "I want to verify a container".
    """
    def __init__(self, x: float, y: float, z: float = 0, target_desc: str = "Location", duration: int = 20):
        super().__init__(f"Investigate({target_desc})")
        self.tx = x
        self.ty = y
        self.tz = z
        self.duration = duration
        self.has_moved = False
        self.timer = 0
        
    def execute(self, state: BrainState) -> List[Action]:
        # Check distance
        px, py = state.player.position.x, state.player.position.y
        dist = math.dist((px, py), (self.tx, self.ty))
        
        if dist < 1.5:
             # Arrived. Wait a bit to let Vision update memory.
             if self.timer == 0:
                 self.timer = self.duration
                 # Convert ticks to ms for the Action (approx 100ms per tick in theory, but here we just pass a value)
                 # Actually, ActionType.WAIT uses MS. Let's assume 1 tick = 100ms for calculation
                 return [Action(ActionType.WAIT.value, {"duration": self.duration * 100})]
             
             self.timer -= 1
             if self.timer <= 0:
                 self.complete()
                 return []
             return []
             
        if not self.has_moved:
            self.has_moved = True
            return [Action(ActionType.MOVE_TO.value, {"x": self.tx, "y": self.ty, "z": self.tz})]
            
        return []
