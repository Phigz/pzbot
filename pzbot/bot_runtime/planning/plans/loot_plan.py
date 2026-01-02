import math
from typing import List

from bot_runtime.brain.state import BrainState
from bot_runtime.control.action_queue import Action, ActionType
from bot_runtime.planning.base import Plan, PlanStatus

class LootPlan(Plan):
    """
    FSM for looting a specific item or container.
    Steps:
    1. Navigate to target (within reach).
    2. If container, ensure open.
    3. Loot item.
    4. Wait for completion.
    """
    
    def __init__(self, target_id: str, container_id: str = None):
        super().__init__(f"Loot({target_id})")
        self.target_id = target_id
        self.container_id = container_id
        
        # FSM State
        self.has_requested_move = False
        self.has_requested_open = False
        self.has_requested_loot = False
        self.wait_timer = 0
        
    def execute(self, state: BrainState) -> List[Action]:
        actions = []
        
        # 1. Locate Target
        # In future, we look up target in Memory. For now, we assume it's in Vision.
        # Check Vision for Item or Container
        target_obj = None
        target_pos = None
        
        # If we have a container ID, that's our physical target
        phys_id = self.container_id if self.container_id else self.target_id
        
        # Find object in vision
        # Note: Vision.objects is list of WorldObject. Interactibles are in there too?
        # Or checking nearby_containers / world_items
        
        # Search containers
        found = False
        for c in state.environment.nearby_containers:
            # Container objects don't always have IDs in current schema? 
            # Assuming we can match by some ID or we navigate to coordinates.
            # TODO: Improve Container Schema to include UUID.
            # For now, let's assume valid ID match or we fail.
             pass 

        # Scan for World Items (floor)
        for item in state.vision.world_items:
             if item.id == self.target_id:
                 target_pos = item
                 found = True
                 break
                 
        # If not found yet, check generic objects (maybe it's a corpse?)
        if not found and not target_pos:
             for obj in state.vision.objects:
                 if obj.id == phys_id:
                     target_pos = obj
                     found = True
                     break
        
        if not found:
            # If we can't see it, we can't loot it.
            # Ideally we check Memory here.
            self.fail(f"Target {phys_id} not in vision/memory")
            return []
            
        # 2. Check Distance
        player_pos = state.player.position
        dist = math.dist((player_pos.x, player_pos.y), (target_pos.x, target_pos.y))
        
        INTERACT_RANGE = 1.5
        
        if dist > INTERACT_RANGE:
            # Phase: Navigate
            if not self.has_requested_move or state.player.action_state.status == "idle":
                 # Emit Move
                 actions.append(Action(ActionType.MOVE_TO.value, {
                     "x": target_pos.x,
                     "y": target_pos.y,
                     "z": getattr(target_pos, 'z', 0)
                 }))
                 self.has_requested_move = True
            return actions
            
        # 3. Arrived -> Open Container (if applicable)
        # TODO: Check if container is open. Current state schema might not expose 'open' status nicely yet.
        # Assuming open for now, or world items don't need opening.
        
        # 4. Looting
        if not self.has_requested_loot:
            actions.append(Action(ActionType.LOOT.value, {
                "targetId": phys_id if self.container_id else "floor", # or specific ID
                "itemId": self.target_id
            }))
            self.has_requested_loot = True
            self.wait_timer = 20 # Wait 20 ticks (approx 2s) for result
            return actions
            
        # 5. Verification
        # Check if item is in inventory
        for inv_item in state.player.inventory:
            if inv_item.id == self.target_id or inv_item.type == self.target_id: # ID or Type match
                self.complete()
                return []
                
        # Timeout check
        self.wait_timer -= 1
        if self.wait_timer <= 0:
            self.fail("Loot timeout - Item did not appear in inventory")
            
        # If waiting, return empty
        return []

