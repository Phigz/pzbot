from bot_runtime.strategy.base import Strategy
from bot_runtime.brain.state import BrainState, SituationMode
from bot_runtime.control.action_queue import ActionQueue
import logging
from bot_runtime.planning.planner import ActionPlanner
from bot_runtime.planning.plans.loot_plan import LootPlan
from bot_runtime.planning.plans.search_building_plan import SearchBuildingPlan
from bot_runtime.planning.plans.investigate_plan import InvestigatePlan

logger = logging.getLogger(__name__)

class LootStrategy(Strategy):
    """
    Handles opportunisitic looting with dynamic needs analysis.
    """

    @property
    def name(self) -> str:
        return "Loot"

    def evaluate(self, state: BrainState) -> float:
        # Boost score slightly if we have a Preparedness Need
        base_score = 0.0
        if state.situation.current_mode == SituationMode.OPPORTUNITY:
            if state.situation.primary_driver == "Need Equipment":
                base_score = 70.0 # Higher priority than generic opportunity
            else:
                base_score = 50.0
        return base_score

    def score_item(self, item, state: BrainState) -> float:
        """
        Dynamically score items based on current needs.
        """
        score = 0.0
        name = item.get('name', '').lower()
        itype = item.get('type', '').lower()
        
        # 1. Clothing (If Naked/Minimal)
        worn_count = len(state.player.worn_items or [])
        if worn_count < 2:
            # High priority for ANY clothing if basically naked
            if "clothing" in itype or "shoes" in name or "pants" in name or "shirt" in name:
                score += 100.0
        
        # 2. Weapons
        if "weapon" in itype:
            score += 10.0
            
        # 3. Bags
        if "container" in itype and "bag" in name:
            score += 50.0
            
        return score

    def execute(self, state: BrainState, queue: ActionQueue, planner: ActionPlanner = None):
        if not planner:
             queue.add("Wait", duration=100)
             return

        # 1. Check Specific Items (Floor or Known in Open Containers)
        targets = state.loot.high_value_targets # Already analyzed by Brain? 
        # Ideally we re-analyze here with our specific scoring
        
        # Manual Scan of Visible Items
        best_item = None
        best_score = 0.0
        
        all_items = []
        if state.vision.world_items: all_items.extend(state.vision.world_items)
        if state.vision and state.vision.nearby_containers:
            for c in state.vision.nearby_containers:
                if c.items:
                    for i in c.items:
                        # Flatten
                        item_data = i.dict()
                        item_data['container_id'] = c.id
                        item_data['x'] = c.x
                        item_data['y'] = c.y
                        all_items.append(item_data)
                        
        for item in all_items:
            # Memory Filter
            if str(item.get('id')) in state.memory.failed_loot_items:
                continue

            # Vertical Filter: Strict Z-Level Match
            # We cannot reach items on other floors without stairs logic (which is separate)
            player_z = state.player.position.z if state.player else 0
            item_z = item.get('z', 0)
            if int(item_z) != int(player_z):
                # logger.debug(f"Skipping item {item.get('name')} on Z={item_z} (Player Z={int(player_z)})")
                continue

            s = self.score_item(item, state)
            if s > best_score:
                best_score = s
                best_item = item
                
        if best_item and best_score > 20.0:
            logger.info(f"[LOOT_STRAT] Found High Value Item: {best_item.get('name')} (Score: {best_score})")
            target_id = best_item.get('id')
            container_id = best_item.get('container_id')
            
            # Prevent flapping
            current_plan = planner.active_plan
            if isinstance(current_plan, LootPlan) and getattr(current_plan, 'target_id', None) == target_id:
                # Already working on this exact item. Let it ride.
                pass
            else:
                planner.set_goal(LootPlan(target_id=target_id, container_id=container_id))
            return

        # 2. Search Building (Exploration)
        # If we see no good loot, but we are inside, search rooms.
        # Fallback to investigate containers if SearchBuilding isn't active
        
        # If we are already searching, let it continue.
        # But Strategy.execute runs every tick.
        # If we return without setting goal, current plan continues?
        # Yes, Planner only changes if set_goal is called.
        
        # How to detect if we should start Searching?
        # If Idle?
        if planner.is_idle():
             # If inside (heuristic: see walls/rooms)
             if state.vision.tiles and any(t.room for t in state.vision.tiles):
                 logger.info("[LOOT_STRAT] Inside building. Starting Search.")
                 px, py = int(state.player.position.x), int(state.player.position.y)
                 planner.set_goal(SearchBuildingPlan(px, py, mode="LOOT_AS_YOU_GO"))
                 return
                 
             # Else wander/investigate containers
             container_targets = state.loot.container_targets
             if container_targets:
                 best_cont = container_targets[0]
                 planner.set_goal(InvestigatePlan(best_cont['x'], best_cont['y'], 0, f"Container_{best_cont['id']}"))
                 return
                 
        # If nothing matches, we do nothing (Planner stays idle or continues current plan)

