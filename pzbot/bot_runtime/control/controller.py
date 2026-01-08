import logging
import json
import os
from typing import Optional
from bot_runtime import config as bot_config
from bot_runtime.ingest.state import GameState
from bot_runtime.world.model import WorldModel
from bot_runtime.control.action_queue import ActionQueue
from bot_runtime.io.input_writer import InputWriter
from bot_runtime.world.logger import WorldLogger
from bot_runtime.input.service import InputService
from bot_runtime.brain.brain import Brain

logger = logging.getLogger(__name__)

from bot_runtime.strategy.decision_engine import DecisionEngine
from bot_runtime.strategy.implementations.idle import IdleStrategy
from bot_runtime.strategy.implementations.survival import SurvivalStrategy
from bot_runtime.strategy.implementations.loot import LootStrategy
from bot_runtime.strategy.implementations.loot_building import LootBuildingStrategy
from bot_runtime.planning.planner import ActionPlanner

class BotController:
    def __init__(self, world_model: WorldModel, action_queue: ActionQueue, input_writer: InputWriter):
        self.world_model = world_model
        self.action_queue = action_queue
        self.input_writer = input_writer
        
        self.world_logger = WorldLogger(self.world_model)
        
        # Initialize Input Service (Hybrid Architecture)
        self.input_service = InputService.get_provider()
        
        # Initialize The Brain
        self.brain = Brain(self.world_model)
        
        # Initialize Planner (Tier 3.5)
        self.planner = ActionPlanner()
        
        # Initialize Strategy Layer (Tier 3)
        # Note: DecisionEngine now takes Planner instead of/in addition to Queue?
        # Actually Strategies set goals on the Planner. The Planner outputs to the Queue.
        # So DecisionEngine needs access to Planner.
        self.decision_engine = DecisionEngine(self.action_queue, self.planner)
        self.decision_engine.register_strategy(IdleStrategy())
        self.decision_engine.register_strategy(SurvivalStrategy())
        self.decision_engine.register_strategy(LootStrategy())
        self.decision_engine.register_strategy(LootBuildingStrategy())

    def on_tick(self, game_state: GameState):
        """Called whenever a new game state is received."""
        # 1. Update World Model
        self.world_model.update(game_state)

        # 2. Update Brain (Analysis)
        self.brain.update()
        
        # 3. Decision Making (Strategy Selection)
        # Strategies evaluate state and set goals on the Planner
        self.decision_engine.decide(self.brain.state)
        
        # 3.5. Planning (FSM)
        # Planner ticks the active plan and emits atomic actions to the Queue
        plan_actions = self.planner.update(self.brain.state)
        
        # Sync Status to Brain State for UI
        if self.planner.active_plan:
            self.brain.state.active_plan_name = self.planner.active_plan.name
            self.brain.state.plan_status = self.planner.active_plan.status.value
        else:
            self.brain.state.active_plan_name = "None"
            self.brain.state.plan_status = "Idle"
            
        if plan_actions:
            for a in plan_actions:
                self.action_queue.add(a)

        # 4. Log World Status

        # 4. Log World Status
        self.world_logger.update()
        
        # 5. Log Brain Activity (Throttle to every ~2s / 20 ticks)
        b = self.brain.state
        if self.world_model.tick_count % 20 == 0:
            
            # Threat
            t_lvl = b.threat.global_level
            t_vec = len(b.threat.vectors)
            
            # Needs
            needs_str = ", ".join([f"{n.name}:{n.score:.0f}" for n in b.needs.active_needs]) or "None"
            
            # Recent Thought
            last_thought = b.active_thought.message if b.active_thought else "..."
            
            plan_info = f"{b.active_plan_name}({b.plan_status})"
            
            logger.info(f"[CORTEX] Threat: {t_lvl:.1f}% ({t_vec} vec) | Plan: {plan_info} | Needs: [{needs_str}] | Thought: \"{last_thought}\"")
            
            # Log Vitals specifically as requested
            if game_state.player and game_state.player.body:
                body = game_state.player.body
                # Sanitize scale (if > 1.0 assume 0-100 scale)
                hp = body.health if body.health <= 1.0 else body.health / 100.0
                stam = body.stamina if body.stamina <= 1.0 else body.stamina / 100.0
                hung = body.hunger if body.hunger <= 1.0 else body.hunger / 100.0
                thirst = body.thirst if body.thirst <= 1.0 else body.thirst / 100.0
                
                logger.info(f"[VITALS] HP:{hp*100:.0f}% Stamina:{stam*100:.0f}% Hunger:{hung*100:.0f}% Thirst:{thirst*100:.0f}%")

        # 6. Flush Action Queue
        actions = []
        if self.action_queue.has_actions():
             actions = self.action_queue.pop_all()
             
             # Visualize Intent (Always)
             b.proposed_actions = actions
        
        # Check Control Config (Safety Gate)
        # 1. Update Safety Lock based on Game State (Paused? Lua Toggle?)
        autopilot = self.input_service.check_safety(game_state)
        
        # 2. Optional: Local Runtime Config Override (Web UI)
        # We can implement an AND condition here if we want a separate "Kill Switch"
        try:
            ctl_path = bot_config.BASE_DIR / "config" / "runtime_control.json"
            if ctl_path.exists():
                with open(ctl_path, 'r') as f:
                    data = json.load(f)
                    # If local config says False, force False
                    if not data.get("autopilot", True): 
                        autopilot = False
                        self.input_service.get_provider().set_safety_lock(True)
        except Exception:
            pass

        # Write to File ONLY if Autopilot is enabled
        if actions and autopilot:
             # logger.info(f"Autopilot Executing {len(actions)} actions.")
             
             physical_actions = []
             logical_actions = []
             
             for action in actions:
                 # Hybrid Dispatch
                 # Simple heuristic: If it's a known physical move, use InputService.
                 # Else, use Lua Injection.
                 
                 # Note: "Walk" currently maps to Lua Pathfinding (WalkTo). 
                 # If we want direct control, we'd use "Move" or "WalkDirect".
                 # For now, let's map Combat/Simple actions.
                 
                 if action.type == 'Attack':
                     self.input_service.click()
                     # Don't buffer physical actions for file write
                 elif action.type == 'Shove':
                     self.input_service.press('space')
                 elif action.type == 'ToggleSneak':
                     self.input_service.press('c')
                 elif action.type == 'DirectMove':
                     # New action type for raw input: { "direction": "w", "duration": 0.5 }
                     d = action.params.get('direction', 'w')
                     t = action.params.get('duration', 0.1)
                     self.input_service.hold(d, t)
                 else:
                     logical_actions.append(action)
             
             # Execute Logical Actions via Lua
             if logical_actions:
                self.input_writer.write_actions(logical_actions)
                
        elif actions:
             # logger.debug("Shadow Mode: Actions proposed but inhibited.")
             pass
