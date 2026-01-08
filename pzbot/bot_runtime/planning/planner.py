from typing import List, Optional
import logging

from bot_runtime.brain.state import BrainState
from bot_runtime.control.action_queue import Action
from bot_runtime.planning.base import Plan, PlanStatus

logger = logging.getLogger(__name__)

class ActionPlanner:
    """
    Tier 3.5 System.
    Manages the lifecycle of persistent Plans (FSMs).
    """
    def __init__(self):
        self.active_plan: Optional[Plan] = None
        self.last_emitted_action_id: Optional[str] = None
        
    def is_idle(self) -> bool:
        return self.active_plan is None

        
    def set_goal(self, plan: Plan, force: bool = False):
        """
        Assigns a new plan.
        If a plan is already running, this will overwrite it based on logic 
        (currently simple overwrite, but could add priority checks).
        """
        if self.active_plan:
            if self.active_plan.status == PlanStatus.RUNNING and not force:
                if self.active_plan.name == plan.name:
                    # Same plan type, maybe just let it run?
                    # For now, always overwrite to ensure responsiveness to new goals
                    # But if we want persistence (e.g. don't reset Loot progress), we would check params.
                    pass
        
        logger.info(f"[PLANNER] Setting new goal: {plan.name} ({plan.id})")
        self.active_plan = plan
        self.last_emitted_action_id = None # Reset pending action on new plan
        
        # Stuck Detection Monitoring
        self.monitor_pos = (0,0)
        import time
        self.last_progress_time = time.time()
        self.stuck_timeout = 15.0 # Seconds stationary before declared stuck
        
    def update(self, state: BrainState) -> List[Action]:
        """
        Called every tick. Advances the active plan.
        """
        if not self.active_plan:
            return []
            
        # Stuck Detection
        import time
        import math
        px, py = state.player.position.x, state.player.position.y
        dist = math.sqrt((px - self.monitor_pos[0])**2 + (py - self.monitor_pos[1])**2)
        
        if dist > 0.5:
            # Significant movement, reset timer
            self.monitor_pos = (px, py)
            self.last_progress_time = time.time()
        else:
            # Stationary
            if self.active_plan.status == PlanStatus.RUNNING:
                if time.time() - self.last_progress_time > self.stuck_timeout:
                    logger.warning(f"[PLANNER] STUCK DETECTED. Plan {self.active_plan.name} stationary for {self.stuck_timeout}s. Aborting.")
                    self.active_plan.fail("Stuck (Stationary)")
                    # Reset timer to prevent spam if strategy immediately restarts it
                    self.last_progress_time = time.time() 
                    return []

            
        # 0. Check Plumbing (Action Feedback)
        if self.last_emitted_action_id:
            astate = state.player.action_state
            
            # Is it currently executing?
            if astate.current_action_id == self.last_emitted_action_id:
                # logger.debug(f"[PLANNER] Waiting for execution of {self.last_emitted_action_id}")
                return []
                
            # Is it just finished?
            if astate.last_completed_action_id == self.last_emitted_action_id:
                logger.info(f"[PLANNER] Action {self.last_emitted_action_id} completed. Proceeding.")
                self.last_emitted_action_id = None
            
            # Is it still in queue (but not executing)?
            # Lua reports 'queue_busy'. If queue is busy, we might assume our action is in there?
            # Ideally we check 'queue_depth', but IDs are better.
            # If we don't see it in executing OR completed, and it's been < X seconds, assume queued.
            # For simplicity: If queue_busy is True, we wait.
            # BUT: We need to handle "Lost Actions" (timeout).
            # TODO: Add timeout logic.
            
            # 0. Check Plumbing (Action Feedback)
        if self.last_emitted_action_id:
            astate = state.player.action_state
            
            # Is it currently executing?
            if astate.current_action_id == self.last_emitted_action_id:
                # logger.debug(f"[PLANNER] Waiting for execution of {self.last_emitted_action_id}")
                from bot_runtime.io.action_logger import ActionLogger
                ActionLogger.feedback(self.last_emitted_action_id, "EXECUTING")
                return []
                
            # Is it just finished?
            # Check both single last_completed (legacy/fallback) and the full completed set (burst handling)
            is_completed = (astate.last_completed_action_id == self.last_emitted_action_id)
            if not is_completed and hasattr(astate, 'completed_ids'):
                is_completed = self.last_emitted_action_id in astate.completed_ids

            if is_completed:
                logger.info(f"[PLANNER] Action {self.last_emitted_action_id} completed (Confirmed). Proceeding.")
                from bot_runtime.io.action_logger import ActionLogger
                ActionLogger.feedback(self.last_emitted_action_id, "COMPLETE", astate.last_completed_result)
                self.last_emitted_action_id = None
            
            if self.last_emitted_action_id and astate.queue_busy:
                 # It's likely in queue.
                 return []
            
            # If we are here, it's not executing, not completed, and queue is empty?
            # It might have failed silently or been wiped.
            # We proceed to let the Plan retry.
            if self.last_emitted_action_id:
                 logger.warning(f"[PLANNER] Action {self.last_emitted_action_id} vanished from execution/queue. Assuming failed/dropped.")
                 from bot_runtime.io.action_logger import ActionLogger
                 ActionLogger.vanished(self.last_emitted_action_id)
                 self.last_emitted_action_id = None
            
        plan = self.active_plan
        
        # If plan is finished/failed, clear it
        if plan.status in [PlanStatus.COMPLETE, PlanStatus.FAILED]:
            logger.info(f"[PLANNER] Plan {plan.name} ended: {plan.status}")
            self.active_plan = None
            return []
            
        # Execute logic
        try:
            if plan.status == PlanStatus.PENDING:
                plan.status = PlanStatus.RUNNING
                
            actions = plan.execute(state)
            
            if actions:
                # Track the LAST action (assuming sequential dependency)
                self.last_emitted_action_id = actions[-1].id
                logger.info(f"[PLANNER] Emitting {len(actions)} actions. Tracking: {self.last_emitted_action_id}")
                
                from bot_runtime.io.action_logger import ActionLogger
                for a in actions:
                    ActionLogger.emit(a.id, a.type, a.params)
            
            # Check status again after execution
            if plan.status == PlanStatus.FAILED:
                logger.warning(f"[PLANNER] Plan {plan.name} Failed: {plan.error_message}")
                
            return actions
            
        except Exception as e:
            logger.error(f"[PLANNER] Critical error in plan {plan.name}: {e}", exc_info=True)
            plan.fail(f"Exception: {e}")
            return []
