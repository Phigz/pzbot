from typing import List, Optional
from bot_runtime.world.model import WorldModel
from bot_runtime.analysis.base import BaseAnalyzer
from bot_runtime.analysis.threat import ThreatAnalyzer
from bot_runtime.analysis.needs import NeedAnalyzer
from bot_runtime.brain.state import BrainState, CharacterPersonality, Thought

class Brain:
    """
    The orchestrator of the bot's mind.
    Manages Analyzers and maintains the BrainState.
    Does NOT make decisions (Strategy Layer) or actions (Planning Layer).
    """
    def __init__(self, world_model: WorldModel):
        self.memory = world_model
        
        # Default Personality (Balanced)
        self.personality = CharacterPersonality()
        
        # Initialize Analysis Modules
        self.analyzers: List[BaseAnalyzer] = [
            ThreatAnalyzer(self.personality),
            NeedAnalyzer(self.personality)
        ]
        
        # The Mental State
        self.state = BrainState()

    def update(self):
        """
        Run one cognitive cycle.
        1. Perception is already done (WorldModel is updated).
        2. Analysis: Derive meaning from facts.
        """
        
        # 1. Clear transient thoughts from previous tick? 
        # Ideally we keep a log, but for state.json we want 'current status'.
        # Let's keep a history but refresh the snapshot.
        current_threat = None
        current_needs = None
        
        new_thoughts = []
        
        # 2. Run Analyzers
        for analyzer in self.analyzers:
            result = analyzer.analyze(self.memory)
            
            if isinstance(analyzer, ThreatAnalyzer):
                current_threat = result
                # Log high threat
                if result.global_level > 50:
                    new_thoughts.append(Thought("THREAT", f"High Danger ({result.global_level:.1f}) detected!", result.global_level))
                    
            elif isinstance(analyzer, NeedAnalyzer):
                current_needs = result
                # Log top need
                top = result.get_highest()
                if top and top.score > 50:
                    new_thoughts.append(Thought("NEED", f"Urgent Need: {top.name} ({top.score:.1f})", top.score))
        
        # 3. Update State
        if current_threat:
            self.state.threat = current_threat
        if current_needs:
            self.state.needs = current_needs
            
        # Append thoughts (limit history to last 50 for now)
        self.state.thoughts.extend(new_thoughts)
        if len(self.state.thoughts) > 50:
             self.state.thoughts = self.state.thoughts[-50:]
             
    def set_personality(self, p: CharacterPersonality):
        self.personality = p
        # Propagate to analyzers
        for a in self.analyzers:
            a.personality = p
