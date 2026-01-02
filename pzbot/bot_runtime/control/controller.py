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

logger = logging.getLogger(__name__)

from bot_runtime.brain.brain import Brain

logger = logging.getLogger(__name__)

from bot_runtime.strategy.decision_engine import DecisionEngine
from bot_runtime.strategy.implementations.idle import IdleStrategy
from bot_runtime.strategy.implementations.survival import SurvivalStrategy
from bot_runtime.strategy.implementations.loot import LootStrategy

class BotController:
    def __init__(self, world_model: WorldModel, action_queue: ActionQueue, input_writer: InputWriter):
        self.world_model = world_model
        self.action_queue = action_queue
        self.input_writer = input_writer
        
        self.world_logger = WorldLogger(self.world_model)
        
        # Initialize The Brain
        self.brain = Brain(self.world_model)
        
        # Initialize Strategy Layer
        self.decision_engine = DecisionEngine(self.action_queue)
        self.decision_engine.register_strategy(IdleStrategy())
        self.decision_engine.register_strategy(SurvivalStrategy())
        self.decision_engine.register_strategy(LootStrategy())

    def on_tick(self, game_state: GameState):
        """Called whenever a new game state is received."""
        # 1. Update World Model
        self.world_model.update(game_state)

        # 2. Update Brain (Analysis)
        self.brain.update()
        
        # 3. Decision Making (Strategy Selection)
        self.decision_engine.decide(self.brain.state)

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
            
            logger.info(f"[CORTEX] Threat: {t_lvl:.1f}% ({t_vec} vec) | Needs: [{needs_str}] | Thought: \"{last_thought}\"")
            
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
        
        # Check Control Config
        autopilot = False
        try:
            ctl_path = bot_config.BASE_DIR / "config" / "runtime_control.json"
            if ctl_path.exists():
                with open(ctl_path, 'r') as f:
                    data = json.load(f)
                    autopilot = data.get("autopilot", False)
        except Exception:
            pass

        # Write to File ONLY if Autopilot is enabled
        if actions and autopilot:
             # logger.info(f"Autopilot Executing {len(actions)} actions.")
             self.input_writer.write_actions(actions)
        elif actions:
             # logger.debug("Shadow Mode: Actions proposed but inhibited.")
             pass
