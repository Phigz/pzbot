import logging
import logging.handlers
from pathlib import Path
import shutil
import datetime
from bot_runtime import config

def setup_logging():
    """Configures logging for the application."""
    
    # Archive previous log if it exists
    if config.LOG_FILE_PATH.exists():
        log_dir = config.LOG_FILE_PATH.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")
        archive_name = f"{timestamp}_{config.LOG_FILE_PATH.name}"
        archive_path = log_dir / archive_name
        
        try:
            shutil.move(str(config.LOG_FILE_PATH), str(archive_path))
            print(f"Archived previous log to {archive_path}")
        except Exception as e:
            print(f"Failed to archive log: {e}")

    root_logger = logging.getLogger()
    root_logger.setLevel(config.LOG_LEVEL)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler (Rotating)
    # Rotates at 5MB, keeps 3 backups
    file_handler = logging.handlers.RotatingFileHandler(
        config.LOG_FILE_PATH,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Lower chatter from third-party libs if needed
    # logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.info(f"Logging configured. Level: {config.LOG_LEVEL}, File: {config.LOG_FILE_PATH}")
