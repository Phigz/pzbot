import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field

class BotConfig(BaseModel):
    """
    Centralized configuration for the Bot Runtime.
    Loads from config/config.yaml if present.
    """
    MEMORY_TTL_GLOBAL: int = Field(default=60000)
    MEMORY_TTL_ZOMBIE: int = Field(default=10000)
    MEMORY_TTL_CONTAINER: int = Field(default=300000)
    MEMORY_TTL_VEHICLE: int = Field(default=300000)
    MEMORY_TTL_ITEM: int = Field(default=60000)
    
    VISION_RADIUS_ZOMBIE: int = 50
    VISION_RADIUS_GRID: int = 15
    LOG_LEVEL: str = "INFO"
    
    # Paths (Strings to allow easy config, converted to Path later)
    INPUT_FILE_PATH: str = "../Lua/AISurvivorBridge/input.json"
    STATE_FILE_PATH: str = "../Lua/AISurvivorBridge/state.json"
    LOG_FILE_PATH: str = "logs/runtime.log"

    class Config:
        env_prefix = "PZBOT_"

def load_settings() -> BotConfig:
    # Resolve path: ../config/config.yaml relative to this file
    base_dir = Path(__file__).parent.parent
    config_path = base_dir / "config" / "config.yaml"
    
    config_data = {}
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}
            print(f"Loaded config from {config_path}")
        except Exception as e:
            print(f"Error loading config.yaml: {e}")
            
    # Manually load environment variables (Pydantic V2 BaseModel doesn't do this automatically without BaseSettings)
    # We iterate over the model fields and check if PZBOT_<FIELD_NAME> exists in os.environ
    for field_name in BotConfig.model_fields.keys():
        env_var_name = f"PZBOT_{field_name}"
        if env_var_name in os.environ:
            val = os.environ[env_var_name]
            config_data[field_name] = val
            print(f"Config Override: {field_name} set to {val} from env var")

    return BotConfig(**config_data)

# Global Config Instance
settings = load_settings()

# Module-level exports for backward compatibility / easy access
BASE_DIR = Path(__file__).parent.parent

def resolve_path(p: str) -> Path:
    path = Path(p)
    if path.is_absolute():
        return path
    return BASE_DIR / path

LOG_FILE_PATH = resolve_path(settings.LOG_FILE_PATH)
STATE_FILE_PATH = resolve_path(settings.STATE_FILE_PATH)
INPUT_FILE_PATH = resolve_path(settings.INPUT_FILE_PATH)
POLLING_INTERVAL = 0.1

# Aliases from settings
LOG_LEVEL = settings.LOG_LEVEL
MEMORY_TTL_ZOMBIE = settings.MEMORY_TTL_ZOMBIE
MEMORY_TTL_CONTAINER = settings.MEMORY_TTL_CONTAINER
MEMORY_TTL_VEHICLE = settings.MEMORY_TTL_VEHICLE
MEMORY_TTL_ITEM = settings.MEMORY_TTL_ITEM
MEMORY_TTL_GLOBAL = settings.MEMORY_TTL_GLOBAL
VISION_RADIUS_ZOMBIE = settings.VISION_RADIUS_ZOMBIE
VISION_RADIUS_GRID = settings.VISION_RADIUS_GRID

