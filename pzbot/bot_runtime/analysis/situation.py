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
        # If safe and valuable loot nearby OR if we *Need* equipment (Preparedness)
        prep = get_need("PREPAREDNESS")
        
        if threat.global_level < 20.0: # Moderate safety required for opportunistic behavior
            # High Preparedness Drive (Need Weapon/Clothes)
            if prep > 50.0:
                 state.current_mode = SituationMode.OPPORTUNITY
                 state.primary_driver = "Need Equipment"
                 return state

            # Standard Shiny Thing Syndrome
            if loot.zone_value > 50.0:
                state.current_mode = SituationMode.OPPORTUNITY
                state.primary_driver = "Good Loot"
                return state

        # 4. DEFAULT
        state.current_mode = SituationMode.IDLE
        state.primary_driver = "Waiting"
        
        # 5. STANCE DETERMINATION
        # Calculate recommended stance based on Mode and Environment
        
        # Default
        state.recommended_stance = "Auto"
        
        if state.current_mode == SituationMode.SURVIVAL:
            # Panic/Fleeing -> Sprint
            state.recommended_stance = "Sprint"
            
        elif env.is_sheltered:
            # INDOORS
            # User Preference: "Aim-walk through homes"
            # If we are in "Opportunity" (Looting) or Maintenance, be careful.
            if threat.global_level > 10.0:
                # If ANY threat nearby, Aim to be ready
                state.recommended_stance = "Aim"
            else:
                # Safe indoors? Just walk/run? 
                # Actually, clearing implies we don't know if it's safe.
                # Let's default to "Aim" if we are exploring (Opportunity).
                if state.current_mode == SituationMode.OPPORTUNITY:
                    state.recommended_stance = "Aim"
                else:
                    state.recommended_stance = "Walk" # Maintenance/Idle indoors = relax
                    
        else:
            # OUTDOORS
            # User Preference: "Navigating between houses... usually run"
            if state.current_mode == SituationMode.OPPORTUNITY:
                state.recommended_stance = "Run"
            elif state.current_mode == SituationMode.MAINTENANCE:
                state.recommended_stance = "Run" # Get to bed/food fast
        
        return state
