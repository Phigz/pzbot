from typing import List, Any

class Memory:
    def __init__(self):
        self.short_term_history: List[Any] = []

    def add_event(self, event: Any):
        self.short_term_history.append(event)
        if len(self.short_term_history) > 100:
            self.short_term_history.pop(0)
