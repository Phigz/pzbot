from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time

@dataclass
class CharacterPersonality:
    """
    Defines the behavioral bias of the character.
    Values are generally 0.0 to 1.0.
    """
    bravery: float = 0.5  # Tolerance for threat. High = Fights longer.
    greed: float = 0.5    # Tolerance for risk when loot is involved.
    caution: float = 0.5  # Weight of unknown areas.

@dataclass
class ThreatVector:
    """A specific source of danger."""
    source_id: str
    type: str     # Zombie, Player, Environment
    x: float
    y: float
    score: float  # How dangerous is this specific entity?

@dataclass
class ThreatState:
    """The aggregate perception of danger."""
    global_level: float = 0.0  # 0.0 to 100.0+
    vectors: List[ThreatVector] = field(default_factory=list)

@dataclass
class Need:
    """A specific drive or requirement."""
    name: str     # HUNGER, THIRST, LOOT(Backpack)
    score: float  # 0.0 (Ignored) to 100.0 (Critical)
    meta: Dict = field(default_factory=dict) # Extra context (e.g. item_type for loot)

@dataclass
class NeedState:
    """The aggregate priority of needs."""
    active_needs: List[Need] = field(default_factory=list)
    
    def get_highest(self) -> Optional[Need]:
        if not self.active_needs:
            return None
        return max(self.active_needs, key=lambda n: n.score)

@dataclass
class Thought:
    """A single loggable unit of cognition."""
    category: str  # THREAT, NEED, PLAN
    message: str
    score: float
    timestamp: float = field(default_factory=time.time)

@dataclass
class BrainState:
    """
    The current mental snapshot of the bot.
    This is what the Strategy Engine will read to make decisions.
    """
    threat: ThreatState = field(default_factory=ThreatState)
    needs: NeedState = field(default_factory=NeedState)
    thoughts: List[Thought] = field(default_factory=list)
    intent: Optional[str] = None # Description of current high-level goal
