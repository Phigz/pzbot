from bot_runtime.control.action_queue import ActionQueue

class WaitExecutor:
    def __init__(self, action_queue: ActionQueue):
        self.action_queue = action_queue

    def wait(self, duration_ms: int):
        self.action_queue.add("wait", duration_ms=duration_ms)
