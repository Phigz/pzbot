from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Any
import uuid

from bot_runtime.brain.state import BrainState
from bot_runtime.control.action_queue import Action

class PlanStatus(Enum):
    PENDING = "PENDING"     # Created but not started
    RUNNING = "RUNNING"     # Actively executing
    COMPLETE = "COMPLETE"   # Successfully finished
    FAILED = "FAILED"       # Unable to complete

class Plan(ABC):
    """
    Abstract base class for a multi-tick plan (Finite State Machine).
    """
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.status = PlanStatus.PENDING
        self.error_message: Optional[str] = None
        
    @abstractmethod
    def execute(self, state: BrainState) -> List[Action]:
        """
        Evaluate the current world state and return actions for this tick.
        Should update self.status accordingly.
        """
        pass
        
    def fail(self, reason: str):
        """Helper to mark plan as failed."""
        self.status = PlanStatus.FAILED
        self.error_message = reason
        
    def complete(self):
        """Helper to mark plan as complete."""
        self.status = PlanStatus.COMPLETE
