from bot_runtime.control.action_queue import ActionQueue, ActionType

class InventoryBuilder:
    def __init__(self, action_queue: ActionQueue):
        self.action_queue = action_queue

    def consume(self, item_id: str):
        """Eat or drink the item."""
        self.action_queue.add(ActionType.CONSUME, itemId=item_id)

    def equip_primary(self, item_id: str):
        """Equip in main hand."""
        self.action_queue.add(ActionType.EQUIP, itemId=item_id, slot="primary")
        
    def equip_secondary(self, item_id: str):
        """Equip in off hand."""
        self.action_queue.add(ActionType.EQUIP, itemId=item_id, slot="secondary")

    def drop(self, item_id: str):
        self.action_queue.add(ActionType.DROP, itemId=item_id)
