from bot_runtime.analysis.base import BaseAnalyzer
from bot_runtime.brain.state import NavigationState
from bot_runtime.world.model import WorldModel
import math

class NavigationAnalyzer(BaseAnalyzer):
    """
    Evaluates spatial context and map knowledge.
    
    Active Inputs:
        - memory.grid (SpatialGrid)
        
    Desired Inputs:
        - NavMesh Complexity
        
    Outputs:
        - NavigationState
    """
    
    def analyze(self, memory: WorldModel) -> NavigationState:
        state = NavigationState()
        
        if not memory.player:
            return state
            
        px = int(memory.player.position.x)
        py = int(memory.player.position.y)
        pz = int(memory.player.position.z)
        
        # 1. Constriction (Cardinal Raycast)
        # Measure distance to walls in 4 directions
        # Short distances = Indoors/Hallway = High Constriction
        directions = [(0,1), (0,-1), (1,0), (-1,0)]
        max_dist = 10
        total_dist = 0
        
        for dx, dy in directions:
            dist = max_dist
            for i in range(1, max_dist + 1):
                tx, ty = px + (dx * i), py + (dy * i)
                tile = memory.grid.get_tile(tx, ty, pz)
                
                # If Unknown (None) or Wall (not w), we stop
                # Note: 'w' (walkable) is usually True for floor.
                # If tile exists but w=False, it's a wall/fence.
                # If tile is None, it's unknown void (treat as open or wall? Treat as wall for safety)
                
                is_wall = False
                if tile is None: 
                    # Unknown space. Treat as open? or Wall? 
                    # Treating as open prevents "Fake Constriction" in open void.
                    pass
                elif not tile.is_walkable:
                    is_wall = True
                
                if is_wall:
                    dist = i
                    break
            total_dist += dist
            
        avg_dist = total_dist / 4.0
        # Normalize: Avg 10 = 0.0 Constriction. Avg 1 = 1.0 Constriction.
        # constriction = 1.0 - (avg / max)
        state.local_constriction = max(0.0, 1.0 - (avg_dist / max_dist))

        # 2. Mapped Ratio
        # Calculate knowledge of local area (Radius ~3 chunks = 30x30m radius)
        # We check if chunks exist in memory.grid
        
        chunk_radius = 2
        cx_start = (px // 10) - chunk_radius
        cx_end = (px // 10) + chunk_radius
        cy_start = (py // 10) - chunk_radius
        cy_end = (py // 10) + chunk_radius
        
        total_chunks = 0
        known_chunks = 0
        
        # Access raw grid chunks safely
        with memory.grid._lock:
            for cx in range(cx_start, cx_end + 1):
                for cy in range(cy_start, cy_end + 1):
                    total_chunks += 1
                    if (cx, cy) in memory.grid.chunks:
                        known_chunks += 1
                        
        state.mapped_ratio = known_chunks / max(1, total_chunks)
            
        return state
