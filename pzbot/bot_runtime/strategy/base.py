from abc import ABC, abstractmethod
import logging
from bot_runtime.brain.state import BrainState
from bot_runtime.control.action_queue import ActionQueue

class Strategy(ABC):
    """
    Abstract Base Class for all bot strategies.
    A Strategy encapsulates a specific mode of behavior (e.g. Fleeing, Looting).
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the strategy."""
        pass

    @abstractmethod
    def evaluate(self, state: BrainState) -> float:
        """
        Calculate utility score (0.0 to 100.0) for this strategy 
        based on the current brain state.
        """
        pass

    @abstractmethod
    def execute(self, state: BrainState, queue: ActionQueue):
        """
        Generate and enqueue actions to the ActionQueue.
        """
        pass
