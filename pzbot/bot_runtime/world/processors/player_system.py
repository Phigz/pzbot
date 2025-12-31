import logging
from typing import Optional
from bot_runtime.ingest.state import Player

logger = logging.getLogger(__name__)

class PlayerSystem:
    """
    Manages the player's self-state (position, vitals, inventory).
    """
    def __init__(self):
        self.state: Optional[Player] = None

    def update(self, player_state: Player):
        self.state = player_state

    def get_position(self):
        if self.state:
            return self.state.position
        return None
        
    @property
    def is_ready(self) -> bool:
        return self.state is not None
