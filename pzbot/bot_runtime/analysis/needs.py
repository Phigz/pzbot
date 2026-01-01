import math
from bot_runtime.analysis.base import BaseAnalyzer
from bot_runtime.brain.state import NeedState, Need
from bot_runtime.world.model import WorldModel

class NeedAnalyzer(BaseAnalyzer):
    """
    Calculates Utility Scores for Drives (Hunger, Thirst, Equipment).
    """
    
    def analyze(self, memory: WorldModel) -> NeedState:
        state = NeedState()
        
        if not memory.player:
            return state
            
        # Fix: Player schema has 'body', not 'vitals'
        vitals = memory.player.body
        
        # 1. Physiological Needs (Sigmoid Curves)
        # We want low hunger to score 0, and high hunger to spike to 100.
        
        # Hunger (0.0 - 1.0)
        # Curve: Starts rising at 0.3, Hits 100 at 0.8
        hunger_score = self._calculate_utility(vitals.hunger, 0.3, 0.8)
        state.active_needs.append(Need("HUNGER", hunger_score))
            
        # Thirst (0.0 - 1.0)
        thirst_score = self._calculate_utility(vitals.thirst, 0.3, 0.8)
        state.active_needs.append(Need("THIRST", thirst_score))
            
        # Fatigue (0.0 - 1.0)
        # Now we have real fatigue from Lua! (0.0=Awake, 1.0=Collapsed)
        real_fatigue = vitals.fatigue
        
        # Moodle Check for Fatigue (Tired)
        # "Tired" Moodle: Level 1 (Drowsy) to 4 (Exhausted)
        # We can use this to clamp minimum scores or boost urgency
        tired_level = self._get_moodle_level(memory, "Tired")
        
        if tired_level >= 2: # Tired or worse
            real_fatigue = max(real_fatigue, 0.5 + (tired_level * 0.1))
            
        fatigue_score = self._calculate_utility(real_fatigue, 0.5, 0.95)
        state.active_needs.append(Need("REST", fatigue_score))
             
        # 2. Equipment Needs (Binary / Greed)
        # Check for Backpack using inventory
        # Current Inventory implementation in PlayerSystem is: self.inventory = new_data.inventory
        # It's a dict.
        
        # Simple string check for now
        has_bag = False
        if memory.player.inventory:
            # Fix: Inventory is a list of dicts, not a dict of dicts
            for item in memory.player.inventory:
                # This depends on how inventory is parsed. 
                # Assuming item['type'] or similar exists.
                # For now, let's just leave this placeholder as we haven't implemented robust Inventory parsing yet.
                pass
                
        # If we implement inventory check, we would multiply by (0.5 + self.personality.greed)
        
        # Sort by urgency
        state.active_needs.sort(key=lambda n: n.score, reverse=True)
        
        return state

    def _get_moodle_level(self, memory: WorldModel, moodle_name: str) -> int:
        if not memory.player or not memory.player.moodles:
            return 0
        for m in memory.player.moodles:
            # Moodle object is usually dict from pzbot side: {'name': 'Tired', 'value': 2, ...}
            # Need to check how 'moodles' is typed in Python.
            # state.py says List[Dict].
            if isinstance(m, dict):
                if m.get('name') == moodle_name:
                    return m.get('value', 0)
        return 0

    def _calculate_utility(self, val: float, min_thresh: float, max_thresh: float) -> float:
        """
        Maps a 0-1 value to a 0-100 utility score.
        Below min_thresh = 0.
        Above max_thresh = 100.
        Linear interpolation in between.
        """
        if val <= min_thresh:
            return 0.0
        if val >= max_thresh:
            return 100.0
            
        range_span = max_thresh - min_thresh
        percent_into_range = (val - min_thresh) / range_span
        return percent_into_range * 100.0
