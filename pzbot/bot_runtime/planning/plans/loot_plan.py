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
        self.has_requested_face = False
        self.has_requested_open = False
        self.has_requested_loot = False
        self.wait_timer = 0
        
import logging
logger = logging.getLogger(__name__)

# ... (Previous imports kept in context, but I only replace method guts if possible. 
# actually Since I have whole file in view, I can replace the class method or bulk.
# I'll replace the execute method block roughly.

    def execute(self, state: BrainState) -> List[Action]:
        actions = []
        
        # 1. Locate Target
        phys_id = self.container_id if self.container_id else self.target_id
        target_pos = None
        
        # Search containers from environment
        if not target_pos and state.vision and state.vision.nearby_containers:
             for c in state.vision.nearby_containers:
                 # Check if this container IS the target
                 if str(c.id) == str(phys_id) or str(c.id) == str(self.target_id):
                     target_pos = c
                     break
                 # Check if this container CONTAINS the target item
                 if c.items:
                     for i in c.items:
                         if str(i.id) == str(self.target_id):
                             target_pos = c # We go to the container
                             break
                 if target_pos: break
                 
        # Search World Items (floor)
        if not target_pos and state.vision.world_items:
             for item in state.vision.world_items:
                 if str(item.id) == str(self.target_id):
                     target_pos = item
                     break

        # Search Generic Objects (e.g. Fridge, Wardrobe)
        if not target_pos and state.vision.objects:
             for obj in state.vision.objects:
                 if str(obj.id) == str(phys_id):
                     target_pos = obj
                     break

        if not target_pos:
            self.fail(f"Target {phys_id} not in vision/memory")
            return []
            
        # 2. Check Distance
        player_pos = state.player.position
        # Ensure target has x/y
        if not hasattr(target_pos, 'x'):
             # Fallback
             self.fail("Target found but has no position")
             return []
             
        dist = math.dist((player_pos.x, player_pos.y), (target_pos.x, target_pos.y))
        
        INTERACT_RANGE = 1.3 # Slightly generous for "Reach"
        
        if dist > INTERACT_RANGE:
            # Phase: Navigate
            if not self.has_requested_move or state.player.action_state.status == "idle":
                 logger.info(f"[LootPlan] Dist: {dist:.2f} > {INTERACT_RANGE}. Requesting Move.")
                 # Find adjacent walkable tile if target is not walkable (assumed true for containers)
                 dest_x, dest_y = target_pos.x, target_pos.y
                 
                 # Helper to find adjacent
                 best_dist = 9999
                 found_adj = False
                 
                 # Create a quick lookup for walkability
                 # This is O(N) where N is visible tiles (~800). Acceptable.
                 walkable_map = set()
                 if state.vision.tiles:
                     for t in state.vision.tiles:
                         if t.w: # w = walkable
                             walkable_map.add((t.x, t.y))
                         
                 # Check 8 neighbors
                 candidates = [
                     (0, 1), (0, -1), (1, 0), (-1, 0),
                     (1, 1), (1, -1), (-1, 1), (-1, -1)
                 ]
                 
                 for dx, dy in candidates:
                     nx, ny = target_pos.x + dx, target_pos.y + dy
                     if (nx, ny) in walkable_map:
                         d = math.dist((player_pos.x, player_pos.y), (nx, ny))
                         if d < best_dist:
                             best_dist = d
                             dest_x, dest_y = nx, ny
                             found_adj = True
                             
                 if not found_adj:
                     # Fallback: Just try the target itself (maybe it IS walkable)
                     pass
                     
                 # Emit Move
                 # Use NEW Navigator format with stance
                 stance = "Auto"
                 if dist > 10:
                     stance = "Run"

                 actions.append(Action(ActionType.MOVE_TO.value, {
                     "x": dest_x,
                     "y": dest_y,
                     "z": getattr(target_pos, 'z', 0),
                     "stance": stance
                 }))
                 self.has_requested_move = True
                 logger.info(f"[LootPlan] Move Action Created: {dest_x},{dest_y}")
            return actions
            
        if not self.has_requested_face:
            logger.info(f"[LootPlan] Dist: {dist:.2f} <= {INTERACT_RANGE}. Arrived. Requesting Face.")
            # Face the target (Container or Item)
            actions.append(Action(ActionType.LOOK_TO.value, {
                "x": target_pos.x, 
                "y": target_pos.y
            }))
            self.has_requested_face = True
            return actions

        # 4. Looting
        if not self.has_requested_loot:
            # Using TRANSFER action (or Loot alias)
            # Need to know Source Container ID.
            # If target_pos came from nearby_containers, it has ID.
            # If floor, ID is "floor".
            
            src_container = self.container_id
            if not src_container:
                 # Infer
                 if hasattr(target_pos, 'object_type') and target_pos.object_type != 'InventoryItem':
                     src_container = target_pos.id # The object itself is the container
                 else:
                     src_container = "floor" 
            
            logger.info(f"[LootPlan] Spawning Loot Action. Src: {src_container}, Item: {self.target_id}")

            actions.append(Action(ActionType.LOOT.value, {
                "targetId": src_container, 
                "itemId": self.target_id,
                "destContainerId": "inventory" # Explicitly to player inventory
            }))
            
            self.has_requested_loot = True
            self.wait_timer = 40 # 4s wait
            return actions
            
        # 4. Verification
        for inv_item in state.player.inventory:
            # Check ID match (String comparison safety)
            # Inventory items are Dicts, not Objects
            found_id = inv_item.get('id')
            found_type = inv_item.get('type')
            if str(found_id) == str(self.target_id) or str(found_type) == str(self.target_id): 
                logger.info(f"[LootPlan] Success! Item found in inventory.")
                self.complete()
                return []
                
        # Timeout check
        self.wait_timer -= 1
        if self.wait_timer <= 0:
            logger.warning("[LootPlan] Timed out waiting for item transfer.")
            self.fail("Loot timeout - Item did not appear in inventory")
            
        return []

