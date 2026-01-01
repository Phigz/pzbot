from typing import Tuple
from bot_runtime.analysis.base import BaseAnalyzer
from bot_runtime.brain.state import ThreatState, ThreatVector
from bot_runtime.world.model import WorldModel

class ThreatAnalyzer(BaseAnalyzer):
    """
    Calculates Global Threat Level based on proximity of hostiles.
    """
    
    def analyze(self, memory: WorldModel) -> ThreatState:
        if not memory.player:
            return ThreatState()
            
        px, py = memory.player.position.x, memory.player.position.y
        state = ThreatState()
        
        # 1. Analyze Zombies
        # We check ALL tracked zombies (Live + Memory)
        zombies = memory.get_entities("Zombie")
        
        total_score = 0.0
        
        for z in zombies:
            dist_sq = (z.x - px)**2 + (z.y - py)**2
            
            # Distance Logic: Inverse Square Law
            # A zombie at 1m is 100 threat.
            # A zombie at 5m is 4 threat (100/25).
            # A zombie at 10m is 1 threat (100/100).
            # Limit close proximity to avoid Infinity
            safe_dist_sq = max(dist_sq, 1.0)
            base_score = 100.0 / safe_dist_sq
            
            # Modifiers? (e.g. Is it chasing me?)
            # Currently we don't have 'is_chasing' robustly in EntityData yet, 
            # but we can assume visible zombies are more dangerous than ghosts.
            
            # Add to vectors if significant
            if base_score > 1.0:
                vector = ThreatVector(
                    source_id=z.id,
                    type="Zombie",
                    x=z.x,
                    y=z.y,
                    score=base_score
                )
                state.vectors.append(vector)
                
            total_score += base_score

        # 2. Apply Personality
        # A BRAVE bot (1.0) reduces threat score. 
        # A COWARDLY bot (0.0) amplifies it? 
        # Let's say Bravery 0.5 is baseline.
        # Adjusted = Score * (1.5 - Bravery)
        # Bravery 1.0 -> Score * 0.5 (Half Threat)
        # Bravery 0.0 -> Score * 1.5 (1.5x Threat)
        
        modifier = 1.5 - self.personality.bravery
        state.global_level = min(total_score * modifier, 100.0) # Cap at 100
        
        # Sort vectors by danger
        state.vectors.sort(key=lambda v: v.score, reverse=True)
        
        return state
