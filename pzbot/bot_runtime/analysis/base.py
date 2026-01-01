from abc import ABC, abstractmethod
from typing import Any
from bot_runtime.brain.state import CharacterPersonality
from bot_runtime.world.model import WorldModel

class BaseAnalyzer(ABC):
    """
    Abstract base class for all analysis modules.
    Analyzers take the WorldModel (Facts) and Personality (Bias) 
    and produce specific Context (Meaning).
    """
    def __init__(self, personality: CharacterPersonality):
        self.personality = personality

    @abstractmethod
    def analyze(self, memory: WorldModel) -> Any:
        """
        Derive meaning from the WorldModel.
        Returns a specific State object (ThreatState, NeedState, etc).
        """
        pass
