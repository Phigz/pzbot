from typing import List, Dict, Any
from collections import deque

class ActionQueue:
    def __init__(self):
        self._queue: deque = deque()

    def add(self, action_type: str, **params):
        """Adds an action to the queue."""
        self._queue.append({
            "type": action_type,
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
