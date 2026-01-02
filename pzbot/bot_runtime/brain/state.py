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
class LootState:
    """Analysis of available resources."""
    zone_value: float = 0.0          # Aggregate value of items in range
    high_value_targets: List[Dict] = field(default_factory=list) # Specific items of interest
    container_targets: List[Dict] = field(default_factory=list)  # Containers worth checking
    best_weapon: Optional[str] = None # Best available weapon ID

@dataclass
class EnvironmentState:
    """Analysis of world conditions."""
    is_daylight: bool = True
    weather_severity: float = 0.0    # 0.0=Clear, 1.0=Storm
    is_sheltered: bool = False       # Indoors/Roofed
    light_level: float = 1.0         # Estimated Lux

@dataclass
class NavigationState:
    """Analysis of spatial context."""
    mapped_ratio: float = 0.0        # % of local chunk known
    local_constriction: float = 0.0  # 0=Open, 1=Tight
    nearest_exit: Optional[tuple] = None # Vector to outside

from enum import Enum, auto

class SituationMode(str, Enum):
    IDLE = "IDLE"
    SURVIVAL = "SURVIVAL"      # Immediate threat to life
    MAINTENANCE = "MAINTENANCE"   # Eating, Sleeping, Healing
    OPPORTUNITY = "OPPORTUNITY"   # Looting, Exploring
    SOCIAL = "SOCIAL"        # Interacting with players

@dataclass
class SituationState:
    """Meta-analysis of the current context."""
    current_mode: SituationMode = SituationMode.IDLE
    primary_driver: str = "None"     # Reason for mode (e.g. "Bleeding")

@dataclass
class BrainState:
    """
    The current mental snapshot of the bot.
    This is what the Strategy Engine will read to make decisions.
    """
    threat: ThreatState = field(default_factory=ThreatState)
    needs: NeedState = field(default_factory=NeedState)
    loot: LootState = field(default_factory=LootState)
    environment: EnvironmentState = field(default_factory=EnvironmentState)
    navigation: NavigationState = field(default_factory=NavigationState)
    situation: SituationState = field(default_factory=SituationState)
    
    thoughts: List[Thought] = field(default_factory=list)
    active_thought: Optional[Thought] = None # The thought generated THIS tick, if any.
    intent: Optional[str] = None # Description of current high-level goal
    active_strategy_name: str = "Init" # The name of the currently running strategy
    proposed_actions: List[Dict] = field(default_factory=list) # Actions the strategy WANTS to execute
