import yaml
from pathlib import Path
from typing import Dict, List, Optional

from bot_runtime import config as bot_config
from bot_runtime.analysis.base import BaseAnalyzer
from bot_runtime.brain.state import LootState, NeedState, CharacterPersonality
from bot_runtime.world.model import WorldModel

class LootAnalyzer(BaseAnalyzer):
    """
    Evaluates the value of items in the effective range (Inventory + Vision).
    Uses 'config/loot.yaml' for base values and applies dynamic multipliers based on Needs/Personality.
    
    Active Inputs:
        - memory.containers
        - NeedState (Context)
    
    Outputs:
        - LootState
    """

    def __init__(self, personality: CharacterPersonality):
        super().__init__(personality)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        path = bot_config.BASE_DIR / "config" / "loot.yaml"
        if not path.exists():
            return {"items": {}, "categories": {}, "multipliers": {}}
        
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {"items": {}, "categories": {}, "multipliers": {}}

    def analyze(self, memory: WorldModel, needs: Optional[NeedState] = None) -> LootState:
        state = LootState()
        
        if not memory.player:
            return state

        # 1. Setup Context Multipliers
        # Default multipliers
        mults = {
            "Food": 1.0,
            "Water": 1.0,
            "Medical": 1.0,
            "Weapon": 1.0,
            "Global": 1.0 + (self.personality.greed * 0.5) # Greed bonus
        }
        
        if needs:
            # Check Need Scores
            # Hunger
            hunger = 0.0
            for n in needs.active_needs:
                if n.name == "HUNGER": hunger = n.score
                if n.name == "THIRST": 
                    if n.score > 50: mults["Water"] *= self.config['multipliers'].get('thirst_high', 2.0)
                if n.name == "MEDICAL":
                     if n.score > 50: mults["Medical"] *= self.config['multipliers'].get('medical_critical', 10.0)

            if hunger > 80:
                mults["Food"] *= self.config['multipliers'].get('hunger_critical', 5.0)
            elif hunger > 50:
                mults["Food"] *= self.config['multipliers'].get('hunger_high', 2.0)
                
        # 2. Evaluate Containers
        containers = memory.memory.containers
        
        total_value = 0.0
        targets = []
        containers_of_interest = []
        
        for cid, container_mem in containers.items():
            c_data = container_mem.data
            items = c_data.properties.get('items', [])
            
            if not items:
                continue
                
            c_value = 0.0
            
            for item in items:
                val, tags = self._get_item_value(item, mults)
                c_value += val
                
                # Interest Threshold
                # Lower threshold if we desperately need it (e.g. food when starving)
                thresh = 30
                if "Food" in tags and mults["Food"] > 2.0: thresh = 10 
                if "Medical" in tags and mults["Medical"] > 2.0: thresh = 10
                
                if val > thresh: 
                    targets.append({
                        "id": item.get('id', 'unknown'),
                        "name": item.get('name', 'Unknown'),
                        "type": item.get('type', 'Unknown'),
                        "x": item.get('x', c_data.x),
                        "y": item.get('y', c_data.y),
                        "value": val,
                        "tags": tags,
                        "container_id": cid
                    })
            
            total_value += c_value
            
            if c_value > 50:
                 containers_of_interest.append({
                     "id": cid,
                     "x": c_data.x,
                     "y": c_data.y,
                     "value": c_value,
                     "item_count": len(items)
                 })

        # 3. Sort Targets
        targets.sort(key=lambda t: t['value'], reverse=True)
        containers_of_interest.sort(key=lambda c: c['value'], reverse=True)
        
        state.zone_value = total_value
        state.high_value_targets = targets
        state.container_targets = containers_of_interest
        
        return state

    def _get_item_value(self, item: Dict, mults: Dict[str, float]) -> tuple[float, List[str]]:
        name = item.get('name', '')
        itype = item.get('type', '') # FullString e.g. Base.Axe
        cat = item.get('category', '')
        
        base_val = 0.0
        tags = []
        
        # 1. Exact Match (Item ID/Type)
        # Check against 'items' in config
        # We need to map short names or full names. Config uses full "Base.Axe".
        # item['type'] usually matches this.
        
        cfg_items = self.config.get('items', {})
        
        if itype in cfg_items:
            entry = cfg_items[itype]
            base_val = float(entry.get('value', 0))
            tags = entry.get('tags', [])
        else:
            # 2. Category Match
            cfg_cats = self.config.get('categories', {})
            # Try to map PZ Category to ours
            # PZ: "Food", "Weapon", "Drainable", "Literature"
            # Config: "Food", "Weapon", "Medical"
            
            # Heuristic for Medical
            if "Bandage" in name or "Pills" in name: cat = "Medical"
            
            if cat in cfg_cats:
                entry = cfg_cats[cat]
                base_val = float(entry.get('value', 0))
                tags = entry.get('tags', [])
            else:
                 # 3. Fallback Keyword Match (Legacy-ish)
                 if "Shotgun" in name: base_val = 80; tags=["Weapon"]
                 elif "Bag" in name: base_val = 100; tags=["Bag"]
                 else: base_val = 1.0 # Scrap
        
        # 3.5 Apply Base Multipliers (Configured Importance)
         # These apply to ALL items with the tag, allowing general tuning
         base_mults = self.config.get('base_multipliers', {})
         for t in tags:
             if t in base_mults:
                 base_val *= float(base_mults[t])

         # 4. Apply Dynamic Multipliers (Context/Needs)
         final_val = base_val * mults.get("Global", 1.0)
        
        for t in tags:
            if t in mults:
                final_val *= mults[t]
                
        return final_val, tags
