import time
import os
import logging
from pathlib import Path
from typing import Callable, Optional
from threading import Thread, Event
from pzbot.bot_runtime.ingest.state import GameState
from pzbot.bot_runtime.ingest.parser import StateParser

logger = logging.getLogger(__name__)

class StateWatcher:
    def __init__(self, state_file_path: Path, on_update: Callable[[GameState], None], polling_interval: float = 0.05):
        self.state_file_path = state_file_path
        self.on_update = on_update
        self.polling_interval = polling_interval
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self._parser = StateParser()
        self._last_mtime = 0.0
        self._last_missing_log = 0.0

    def start(self):
        """Starts the watcher in a background thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Watcher already running.")
            return
        
        self._stop_event.clear()
        self._thread = Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info(f"Started watching {self.state_file_path}")

    def stop(self):
        """Stops the watcher thread."""
        if self._thread:
            self._stop_event.set()
            self._thread.join(timeout=1.0)
            self._thread = None
            logger.info("Stopped watching state file.")

    def _watch_loop(self):
        while not self._stop_event.is_set():
            try:
                if self.state_file_path.exists():
                    stat = self.state_file_path.stat()
                    mtime = stat.st_mtime
                    
                    if mtime > self._last_mtime:
                        self._last_mtime = mtime
                        # Small delay to ensure write completion if needed, though atomic writes are preferred
                        # But for now assuming file is ready when mtime updates or we catch JSON error and retry next time
                        try:
                            game_state = self._parser.parse_file(self.state_file_path)
                            self.on_update(game_state)
                            # logger.debug(f"State updated. Tick: {game_state.tick}")
                        except Exception as e:
                            logger.warning(f"Error parsing state update: {e}")
                else:
                    # Log warning if file is missing, throttled to once every 10s
                    now = time.time()
                    if now - self._last_missing_log > 10:
                        logger.warning(f"State file not found at {self.state_file_path}. Waiting for game...")
                        self._last_missing_log = now

            except Exception as e:
                logger.error(f"Error in watcher loop: {e}")

            time.sleep(self.polling_interval)
