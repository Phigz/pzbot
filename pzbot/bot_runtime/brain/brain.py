from typing import List, Optional
from bot_runtime.world.model import WorldModel
from bot_runtime.analysis.base import BaseAnalyzer
from bot_runtime.analysis.threat import ThreatAnalyzer
from bot_runtime.analysis.needs import NeedAnalyzer
from bot_runtime.analysis.loot import LootAnalyzer
from bot_runtime.analysis.environment import EnvironmentAnalyzer
from bot_runtime.analysis.navigation import NavigationAnalyzer
from bot_runtime.analysis.zones import ZoneAnalyzer
from bot_runtime.analysis.situation import SituationAnalyzer

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
        
        # Tier 1 Analyzers
        self.threat_analyzer = ThreatAnalyzer(self.personality)
        self.need_analyzer = NeedAnalyzer(self.personality)
        self.loot_analyzer = LootAnalyzer(self.personality)
        self.env_analyzer = EnvironmentAnalyzer(self.personality)
        self.nav_analyzer = NavigationAnalyzer(self.personality)
        self.zone_analyzer = ZoneAnalyzer(self.personality) # Phase 5
        
        # Tier 2 Analyzers
        self.situation_analyzer = SituationAnalyzer()
        
        # The Mental State
        self.state = BrainState()

    def update(self):
        """
        Run one cognitive cycle.
        1. Perception is already done (WorldModel is updated).
        2. Analysis: Derive meaning from facts.
        """
        new_thoughts = []
        
        # --- TIER 1 ANALYSIS ---
        threat = self.threat_analyzer.analyze(self.memory)
        needs = self.need_analyzer.analyze(self.memory)
        # Pass needs to loot analyzer for valuation
        loot = self.loot_analyzer.analyze(self.memory, needs)
        env = self.env_analyzer.analyze(self.memory)
        nav = self.nav_analyzer.analyze(self.memory)
        zone = self.zone_analyzer.analyze(self.memory) # New Phase 5
        
        # Logging Thoughts based on Tier 1
        if threat.global_level > 50:
             new_thoughts.append(Thought("THREAT", f"High Danger ({threat.global_level:.1f})!", threat.global_level))
             
        top_need = needs.get_highest()
        if top_need and top_need.score > 50:
             new_thoughts.append(Thought("NEED", f"Urgent: {top_need.name}", top_need.score))

        # --- TIER 2 ANALYSIS ---
        situation = self.situation_analyzer.analyze(needs, threat, loot, env)
        
        # Log Situation Change
        if len(self.state.thoughts) > 0 and self.state.situation.current_mode != situation.current_mode:
             new_thoughts.append(Thought("META", f"Mode Switch: {situation.current_mode.name} ({situation.primary_driver})", 100.0))
        
        # --- UPDATE STATE ---
        self.state.threat = threat
        self.state.needs = needs
        self.state.loot = loot
        self.state.environment = env
        self.state.navigation = nav
        self.state.zone = zone
        self.state.situation = situation
        self.state.vision = self.memory.vision
        self.state.player = self.memory.player
        
        # Update Thought Stream
        if new_thoughts:
            # Pick the most "Urgent" one as the 'active' thought for this tick
            # Sort by score desc
            new_thoughts.sort(key=lambda x: x.score, reverse=True)
            self.state.active_thought = new_thoughts[0]
            
            # Append to history
            self.state.thoughts.extend(new_thoughts)
            if len(self.state.thoughts) > 50:
                 self.state.thoughts = self.state.thoughts[-50:]
        else:
            self.state.active_thought = None
             
    def set_personality(self, p: CharacterPersonality):
        self.personality = p
        # Propagate to analyzers
        self.threat_analyzer.personality = p
        self.need_analyzer.personality = p
        self.loot_analyzer.personality = p
        self.env_analyzer.personality = p
        self.nav_analyzer.personality = p
