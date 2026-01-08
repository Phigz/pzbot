from typing import List, Dict, Any, Union
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import uuid

class ActionType(str, Enum):
    MOVE_TO = "MoveTo"
    WAIT = "Wait"
    LOOK_TO = "LookTo"
    SIT = "Sit"
    ATTACK = "Attack"
    LOOT = "Loot"
    EQUIP = "Equip"
    INTERACT = "Interact"
    CONSUME = "Consume"
    STOP = "Stop"
    DIRECT_MOVE = "DirectMove"
    DROP = "Drop"

@dataclass
class Action:
    type: str # or ActionType
    params: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "params": self.params
        }

class ActionQueue:
    def __init__(self):
        self._queue: deque = deque()

    def add(self, action_or_type: Union[str, Action], **params) -> Action:
        """
        Adds an action to the queue and returns the created Action object (with ID).
        """
        if isinstance(action_or_type, Action):
            act = action_or_type
            if not act.id:
                act.id = str(uuid.uuid4())
        else:
            # Create Action object
            act = Action(
                type=action_or_type, 
                params=params, 
                id=str(uuid.uuid4())
            )

        self._queue.append(act.to_dict())
        return act

    def clear(self):
        self._queue.clear()

    def pop_all(self) -> List[Dict[str, Any]]:
        """Returns all actions in the queue and clears it."""
        actions = list(self._queue)
        self._queue.clear()
        return actions

    def has_actions(self) -> bool:
        return len(self._queue) > 0
