from bot_runtime.brain.state import SituationState, SituationMode, NeedState, ThreatState, LootState, EnvironmentState

class SituationAnalyzer:
    """
    Tier 2 Analyzer.
    Synthesizes outputs from Tier 1 analyzers to determine the high-level 'Mode'.
    
    Inputs:
        - NeedState
        - ThreatState
        - LootState
        - EnvironmentState
        
    Outputs:
        - SituationState
    """
    
    def analyze(self, needs: NeedState, threat: ThreatState, loot: LootState, env: EnvironmentState) -> SituationState:
        state = SituationState()
        
        # Helper to get need score
        def get_need(name):
            for n in needs.active_needs:
                if n.name == name: return n.score
            return 0.0

        # 1. SURVIVAL CHECK (Immediate Danger)
        # High Threat or Critical Medical Issue
        med_score = get_need("MEDICAL")
        
        if threat.global_level > 50.0:
            state.current_mode = SituationMode.SURVIVAL
            state.primary_driver = "High Threat"
            return state
            
        if med_score > 80.0:
            state.current_mode = SituationMode.SURVIVAL
            state.primary_driver = "Critical Condition"
            return state

        # 2. MAINTENANCE CHECK (Physiological Needs)
        # Hunger, Thirst, Fatigue
        hunger = get_need("HUNGER")
        thirst = get_need("THIRST")
        fatigue = get_need("REST")
        
        # Only prioritize maintenance if threat is manageable
        if threat.global_level < 30.0:
            if fat_highest := (fatigue > 80.0):
                state.current_mode = SituationMode.MAINTENANCE
                state.primary_driver = "Exhausted"
                return state
                
            if hunger > 60.0 or thirst > 60.0:
                state.current_mode = SituationMode.MAINTENANCE
                state.primary_driver = "Hungry/Thirsty"
                return state

        # 3. OPPORTUNITY (Looting / Exploring)
        # If safe and valuable loot nearby
        if threat.global_level < 15.0:
            if loot.zone_value > 50.0:
                state.current_mode = SituationMode.OPPORTUNITY
                state.primary_driver = "Good Loot"
                return state

        # 4. DEFAULT
        state.current_mode = SituationMode.IDLE
        state.primary_driver = "Waiting"
        return state
