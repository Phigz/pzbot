import logging
import time
from typing import Optional
from .view import WorldView

logger = logging.getLogger(__name__)

class WorldLogger:
    """
    Logs high-level world state stats to the console/log file.
    Consumes the WorldView interface.
    """
    def __init__(self, world: WorldView, log_interval: float = 5.0):
        self.world = world
        self.log_interval = log_interval
        self.last_log_time = 0.0

    def update(self):
        """Checks if it's time to log and does so if needed."""
        now = time.time()
        if now - self.last_log_time > self.log_interval:
            self.log_status()
            self.last_log_time = now

    def log_status(self):
        """Logs current world status summary."""
        player = self.world.player
        if not player:
            logger.debug("World Status: No Player Data")
            return

        # Use the semantic interface
        zombies = self.world.get_entities("Zombie")
        players = self.world.get_entities("Player")
        
        pos = player.position
        pos_str = f"({pos.x:.1f}, {pos.y:.1f}, {pos.z})"
        
        status = f"Player @ {pos_str} | Zombies: {len(zombies)} | Other Players: {len(players)}"
        
        # Verbose: Log Interactive Objects
        doors = self.world.get_entities("Door")
        windows = self.world.get_entities("Window")
        if doors or windows:
            status += f" | Doors: {len(doors)} | Windows: {len(windows)}"
        
        # Log threat if any close by
        nearest_z = self.world.find_nearest_entity(pos.x, pos.y, "Zombie")
        if nearest_z:
            dist = ((nearest_z.x - pos.x)**2 + (nearest_z.y - pos.y)**2)**0.5
            if dist < 10:
                status += f" | [!] NEAREST THREAT: {dist:.1f}m"

        # Log Grid Stats
        if hasattr(self.world, 'grid'):
            stats = self.world.grid.get_stats()
            status += f" | Mapped: {stats['total_tiles']}"

        logger.debug(status)
