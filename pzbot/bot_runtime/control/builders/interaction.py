from bot_runtime.control.action_queue import ActionQueue, ActionType

class InteractionBuilder:
    def __init__(self, action_queue: ActionQueue):
        self.action_queue = action_queue

    def interact_with(self, target_id: str):
        """Generic interaction (click) on an object."""
        self.action_queue.add(ActionType.INTERACT, targetId=target_id)
    
    def open_door(self, door_id: str):
        """Specifically for doors (might be same as interact in Lua)."""
        self.action_queue.add(ActionType.INTERACT, targetId=door_id)

    def toggle_switch(self, switch_id: str):
        self.action_queue.add(ActionType.INTERACT, targetId=switch_id)
