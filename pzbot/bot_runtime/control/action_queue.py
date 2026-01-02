from typing import List, Dict, Any, Union
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

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
    DROP = "Drop"

@dataclass
class Action:
    type: str # or ActionType
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "type": self.type,
            "params": self.params
        }

class ActionQueue:
    def __init__(self):
        self._queue: deque = deque()

    def add(self, action_or_type: Union[str, Action], **params):
        """
        Adds an action to the queue.
        Can accept:
        1. Action object: queue.add(Action(...))
        2. String type: queue.add("MoveTo", x=10, y=20)
        """
        if isinstance(action_or_type, Action):
            self._queue.append(action_or_type.to_dict())
        else:
            self._queue.append({
                "type": action_or_type,
                "params": params
            })

    def clear(self):
        self._queue.clear()

    def pop_all(self) -> List[Dict[str, Any]]:
        """Returns all actions in the queue and clears it."""
        actions = list(self._queue)
        self._queue.clear()
        return actions

    def has_actions(self) -> bool:
        return len(self._queue) > 0
