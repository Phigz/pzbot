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
        
        if not memory.player or not memory.player.body:
            return state
            
        vitals = memory.player.body
        
        # --- 1. Physiological Needs ---
        
        # Hunger (0.0 - 1.0) -> Score (0-100)
        hunger_score = self._calculate_utility(vitals.hunger, 0.3, 0.8)
        # Multiplier: if "Hungry" Moodle exists
        if self._has_moodle(memory, "Hungry"): hunger_score = max(hunger_score, 50.0)
        state.active_needs.append(Need("HUNGER", hunger_score))

        # Thirst
        thirst_score = self._calculate_utility(vitals.thirst, 0.3, 0.8)
        if self._has_moodle(memory, "Thirst"): thirst_score = max(thirst_score, 50.0)
        state.active_needs.append(Need("THIRST", thirst_score))
        
        # Fatigue / Rest
        real_fatigue = vitals.fatigue
        tired_level = self._get_moodle_level(memory, "Tired")
        if tired_level >= 2: 
            real_fatigue = max(real_fatigue, 0.5 + (tired_level * 0.1))
        
        fatigue_score = self._calculate_utility(real_fatigue, 0.5, 0.95)
        state.active_needs.append(Need("REST", fatigue_score))
        
        # Sanity / Boredom
        # Sanity 1.0 = Good. We want "Insanity" score.
        insanity_val = 1.0 - vitals.sanity
        sanity_score = self._calculate_utility(insanity_val, 0.3, 0.9)
        state.active_needs.append(Need("SANITY", sanity_score))
        
        boredom_score = self._calculate_utility(vitals.boredom, 0.4, 0.9)
        state.active_needs.append(Need("BOREDOM", boredom_score))

        # --- 2. Medical Needs ---
        
        medical_score = 0.0
        medical_meta = []
        
        # Pain
        pain_val = vitals.panic # Assuming 'panic' or specific 'pain' stat if available
        # Actually vitals has 'pain' in parts usually, or moodle. 
        # Checking Moodle "Pain"
        pain_level = self._get_moodle_level(memory, "Pain")
        if pain_level > 0:
            medical_score = max(medical_score, pain_level * 20.0)
            medical_meta.append("Painkillers")
            
        # Bleeding / Wounds
        if vitals.parts:
            for part_name, part in vitals.parts.items():
                # part is a dict from Pydantic model dump usually, or object?
                # Pydantic model: PlayerBody.parts is Dict[str, Any]
                
                if part.get("bleeding", False):
                    medical_score = 100.0 # CRITICAL
                    medical_meta.append(f"Bandage {part_name}")
                if part.get("bitten", False):
                    medical_score = 100.0 # FATAL
                    medical_meta.append(f"Bitten {part_name}")
                if part.get("fracture", False):
                     medical_score = max(medical_score, 80.0)
                     medical_meta.append(f"Splint {part_name}")

        state.active_needs.append(Need("MEDICAL", medical_score, {"issues": medical_meta}))

        # --- 3. Sorting ---
        state.active_needs.sort(key=lambda n: n.score, reverse=True)
        return state

    def _get_moodle_level(self, memory: WorldModel, moodle_name: str) -> int:
        if not memory.player or not memory.player.moodles:
            return 0
        for m in memory.player.moodles:
            # Moodles are dicts: {'name': 'Tired', 'value': 2, ...}
            if m.get('name') == moodle_name:
                return m.get('value', 0)
        return 0
        
    def _has_moodle(self, memory: WorldModel, moodle_name: str) -> bool:
        return self._get_moodle_level(memory, moodle_name) > 0

    def _calculate_utility(self, val: float, min_thresh: float, max_thresh: float) -> float:
        if val <= min_thresh: return 0.0
        if val >= max_thresh: return 100.0
        range_span = max_thresh - min_thresh
        return ((val - min_thresh) / range_span) * 100.0
