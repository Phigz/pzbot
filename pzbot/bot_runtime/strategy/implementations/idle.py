from bot_runtime.strategy.base import Strategy
from bot_runtime.brain.state import BrainState
from bot_runtime.control.action_queue import ActionQueue

class IdleStrategy(Strategy):
    """
    Default behavior. Do nothing but observe.
    Score: Always 1.0 (Baseline).
    """

    @property
    def name(self) -> str:
        return "Idle"

    def evaluate(self, state: BrainState) -> float:
        return 1.0

    def execute(self, state: BrainState, queue: ActionQueue):
        # Only queue waiting if the queue is empty to avoid spamming
        if not queue.has_actions():
            # Wait for 1 second (1000ms)
            queue.add("Wait", duration=1000)
