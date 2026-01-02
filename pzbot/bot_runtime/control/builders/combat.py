from bot_runtime.control.action_queue import ActionQueue, ActionType

class CombatBuilder:
    def __init__(self, action_queue: ActionQueue):
        self.action_queue = action_queue

    def attack(self, target_id: str):
        """Swing equipped weapon at the target entity."""
        self.action_queue.add(ActionType.ATTACK, targetId=target_id)
