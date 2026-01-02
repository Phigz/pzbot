from bot_runtime.strategy.base import Strategy
from bot_runtime.brain.state import BrainState, SituationMode
from bot_runtime.control.action_queue import ActionQueue

class SurvivalStrategy(Strategy):
    """
    Handles critical threats to life (Zombies, Bleeding).
    Score: 100.0 if in SURVIVAL mode.
    """

    @property
    def name(self) -> str:
        return "Survival"

    def evaluate(self, state: BrainState) -> float:
        if state.situation.current_mode == SituationMode.SURVIVAL:
            return 100.0
        return 0.0

    def execute(self, state: BrainState, queue: ActionQueue):
        driver = state.situation.primary_driver
        
        if driver == "High Threat":
            # NAIVE FLEE implementation
            # Determine direction away from center of mass of threats?
            # For now, just Run away from nearest threat vector.
            # Ideally we use NavigationAnalyzer's 'nearest_exit' or calculated vector.
            
            # Placeholder: Just log intent for now
            # queue.add("Say", text="I need to run!")
            
            # Simple Flee: If nearest threat is close, walk opposite?
            # Since we don't have 'WalkTo' vector logic fully wired in ActionClient yet,
            # we will just turn and wait to simulate panic for this step.
            queue.add("Wait", duration=500)
            
        elif driver == "Critical Condition":
            # If bleeding, we should bandage.
            # We need an inventory system to check for bandages.
            # For now, just wait.
            queue.add("Wait", duration=1000)
