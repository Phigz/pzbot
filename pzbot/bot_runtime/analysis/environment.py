from bot_runtime.analysis.base import BaseAnalyzer
from bot_runtime.brain.state import EnvironmentState
from bot_runtime.world.model import WorldModel
import math

class EnvironmentAnalyzer(BaseAnalyzer):
    """
    Evaluates world conditions such as light, weather, and shelter.
    
    Active Inputs:
        - memory.current_state.environment (Time, Rain, Fog)
        - memory.player.vision.tiles (For Room/Shelter check)
        
    Desired Inputs:
        - Light Level (Lux)
        - True Temperature
        
    Outputs:
        - EnvironmentState
    """
    
    def analyze(self, memory: WorldModel) -> EnvironmentState:
        state = EnvironmentState()
        
        env = memory.current_state.environment if memory.current_state else None
        
        # 1. Weather / Daylight
        if env:
            # PZ Time: 0.0 - 24.0
            t = env.time_of_day
            state.is_daylight = (t >= 7.0 and t <= 20.0)
            
            # Severity: Max of rain or fog
            severity = max(env.rain_intensity, env.fog_intensity)
            state.weather_severity = float(severity)
            
            # Temperature?
            # state.py Environment object has it.
        
        # 2. Shelter Check
        # We need to find the tile the player is standing on.
        if memory.player and memory.player.vision and memory.player.vision.tiles:
            px = int(memory.player.position.x)
            py = int(memory.player.position.y)
            pz = int(memory.player.position.z)
            
            # Simple linear search over vision tiles (usually small set ~700)
            # Optimization: Could use GridSystem if indexed
            found_room = False
            for tile in memory.player.vision.tiles:
                if tile.x == px and tile.y == py and tile.z == pz:
                    if tile.room:
                        found_room = True
                    break
            
            state.is_sheltered = found_room
            
        return state
