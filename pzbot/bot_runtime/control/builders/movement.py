from bot_runtime.control.action_queue import ActionQueue

class MovementExecutor:
    def __init__(self, action_queue: ActionQueue):
        self.action_queue = action_queue

    def move_to(self, x: int, y: int, z: int = 0, stance: str = "Auto"):
        # This could involve pathfinding in the future, 
        # but for now we might just emit a "walk_to" action if the game supports it,
        # or "path_find_to".
        self.action_queue.add("path_find_to", x=x, y=y, z=z, stance=stance)
    
    def walk_to_direct(self, x: int, y: int, z: int = 0):
        self.action_queue.add("walk_to", x=x, y=y, z=z)
