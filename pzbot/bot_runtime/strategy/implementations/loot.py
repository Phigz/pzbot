from bot_runtime.strategy.base import Strategy
from bot_runtime.brain.state import BrainState, SituationMode
from bot_runtime.control.action_queue import ActionQueue

class LootStrategy(Strategy):
    """
    Handles opportunisitic looting.
    Score: 50.0 if in OPPORTUNITY mode.
    Action: Walk to high-value target.
    """

    @property
    def name(self) -> str:
        return "Loot"

    def evaluate(self, state: BrainState) -> float:
        if state.situation.current_mode == SituationMode.OPPORTUNITY:
            return 50.0
        return 0.0

    def execute(self, state: BrainState, queue: ActionQueue):
        targets = state.loot.high_value_targets
        
        if not targets:
            # Fallback if mode says Opportunity but targets vanished
            queue.add("Wait", duration=500)
            return

        # Pick best target
        best = targets[0]
        
        # Simple WalkTo
        # Note: Ideally we check if we are already there and 'Grab' it.
        # But for now, just walking.
        
        # Check distance
        # We don't have player pos easily in BrainState unless we add it or read from memory logic.
        # Wait, ActionClient 'MoveTo' handles pathfinding usually?
        # Or simplistic walk.
        
        queue.add("MoveTo", x=best['x'], y=best['y'], z=best.get('z', 0))
