import logging
import time
from bot_runtime.config import BASE_DIR

class ActionLogger:
    """
    Dedicated logger for Action Lifecycle events.
    Writes to a separate file for easier debugging of plumbing issues.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ActionLogger, cls).__new__(cls)
            cls._instance.setup()
        return cls._instance

    def setup(self):
        self.logger = logging.getLogger("action_lifecycle")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False # Do not propagate to root logger (console)

        log_dir = BASE_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "actions.log", mode='w')
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.info("Action Logger Initialized")

    def log_emit(self, action_id: str, action_type: str, params: dict):
        self.logger.info(f"[EMIT] ID:{action_id} TYPE:{action_type} PARAMS:{params}")

    def log_vanished(self, action_id: str):
         self.logger.warning(f"[VANISHED] ID:{action_id} - Never confirmed executing/completed.")

    def log_feedback(self, action_id: str, status: str, result: str = None):
         msg = f"[FEEDBACK] ID:{action_id} STATUS:{status}"
         if result:
             msg += f" RES:{result}"
         self.logger.info(msg)

    @classmethod
    def emit(cls, action_id: str, action_type: str, params: dict):
        cls().log_emit(action_id, action_type, params)
        
    @classmethod
    def vanished(cls, action_id: str):
        cls().log_vanished(action_id)

    @classmethod
    def feedback(cls, action_id: str, status: str, result: str = None):
        cls().log_feedback(action_id, status, result)
