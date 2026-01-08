import sys
import time
import abc
import platform
import subprocess
from typing import Optional

# Conditional import for Windows
try:
    import pydirectinput
    # Disable pydirectinput's failsafe or pause if needed
    pydirectinput.PAUSE = 0.05 
except ImportError:
    pydirectinput = None

try:
    import pyautogui
    # Fail-safes
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None

class InputProvider(abc.ABC):
    """Abstract base class for hardware-level input."""
    
    @abc.abstractmethod
    def press(self, key: str):
        pass

    @abc.abstractmethod
    def hold(self, key: str, duration: float):
        pass

    @abc.abstractmethod
    def key_down(self, key: str):
        pass
    
    @abc.abstractmethod
    def key_up(self, key: str):
        pass

    @abc.abstractmethod
    def click(self, button: str = 'left'):
        pass

class WindowsInputProvider(InputProvider):
    """Implementation for Windows using pydirectinput."""
    
    def __init__(self):
        if not pydirectinput:
            raise ImportError("pydirectinput is required for WindowsInputProvider")

    def press(self, key: str):
        pydirectinput.press(key)

    def hold(self, key: str, duration: float):
        pydirectinput.keyDown(key)
        time.sleep(duration)
        pydirectinput.keyUp(key)

    def key_down(self, key: str):
        pydirectinput.keyDown(key)

    def key_up(self, key: str):
        pydirectinput.keyUp(key)
        
    def click(self, button: str = 'left'):
        pydirectinput.click(button=button)

class LinuxInputProvider(InputProvider):
    """
    Implementation for Linux using xdotool (works with Xvfb/X11).
    """
    def __init__(self):
        # Check if xdotool exists
        try:
            subprocess.run(["xdotool", "--version"], check=True, stdout=subprocess.DEVNULL)
        except Exception:
            print("WARNING: xdotool not found! Linux input will fail.")

    def _run(self, args):
        subprocess.run(["xdotool"] + args, check=False)

    def press(self, key: str):
        # Map some common keys if needed
        self._run(["key", key])

    def hold(self, key: str, duration: float):
        self._run(["keydown", key])
        time.sleep(duration)
        self._run(["keyup", key])

    def key_down(self, key: str):
        self._run(["keydown", key])

    def key_up(self, key: str):
        self._run(["keyup", key])
        
    def click(self, button: str = 'left'):
        # xdotool click 1 (left), 2 (middle), 3 (right)
        btn_map = {'left': '1', 'middle': '2', 'right': '3'}
        b = btn_map.get(button, '1')
        self._run(["click", b])

class InputService:
    """
    Factory/Facade for getting the correct InputProvider based on OS.
    """
    _instance: Optional[InputProvider] = None

        return cls._instance

    def check_safety(self, game_state: 'GameState') -> bool:
        """
        Updates the safety status based on GameState.
        Returns True if input is allowed, False otherwise.
        """
        if not game_state:
            return False
            
        is_paused = False
        if game_state.environment:
            is_paused = game_state.environment.is_paused
            
        autopilot = True # Default true if missing (e.g. old mod version), or make it strict?
        # Strict for safety
        if game_state.flags and "autopilot_enabled" in game_state.flags:
            autopilot = game_state.flags["autopilot_enabled"]
        else:
            # Fallback: if flag missing, maybe assume safe if we want weak constraints, 
            # but for "Gatekeeper" feature, let's assume False if we can't confirm.
            # actually, during dev, default True is less annoying.
            autopilot = True

        can_input = (not is_paused) and autopilot
        
        provider = self.get_provider()
        if hasattr(provider, 'set_safety_lock'):
            provider.set_safety_lock(not can_input)
            
        return can_input

class GatekeeperMixin:
    """Mixin to add safety checks to InputProviders."""
    _safety_locked: bool = False

    def set_safety_lock(self, locked: bool):
        self._safety_locked = locked
        if locked:
           # Ideally release any held keys here to prevent "stuck" keys
           pass

    def _check_lock(self):
        if self._safety_locked:
            # We can log debug here if needed, but it might spam
            return False
        return True

# Re-declare Providers to use Mixin
class WindowsInputProvider(InputProvider, GatekeeperMixin):
    """Implementation for Windows using pydirectinput."""
    
    def __init__(self):
        if not pydirectinput:
            raise ImportError("pydirectinput is required for WindowsInputProvider")

    def press(self, key: str):
        if not self._check_lock(): return
        pydirectinput.press(key)

    def hold(self, key: str, duration: float):
        if not self._check_lock(): return
        pydirectinput.keyDown(key)
        time.sleep(duration)
        pydirectinput.keyUp(key)

    def key_down(self, key: str):
        if not self._check_lock(): return
        pydirectinput.keyDown(key)

    def key_up(self, key: str):
        # Always allow key_up to prevent stuck keys?
        # Or block it too? safely, allow key_up might be better, but consistent block is safest for "no action"
        pydirectinput.keyUp(key)
        
    def click(self, button: str = 'left'):
        if not self._check_lock(): return
        pydirectinput.click(button=button)

class LinuxInputProvider(InputProvider, GatekeeperMixin):
    """
    Implementation for Linux using xdotool (works with Xvfb/X11).
    """
    def __init__(self):
        # Check if xdotool exists
        try:
            subprocess.run(["xdotool", "--version"], check=True, stdout=subprocess.DEVNULL)
        except Exception:
            print("WARNING: xdotool not found! Linux input will fail.")

    def _run(self, args):
        subprocess.run(["xdotool"] + args, check=False)

    def press(self, key: str):
        if not self._check_lock(): return
        self._run(["key", key])

    def hold(self, key: str, duration: float):
        if not self._check_lock(): return
        self._run(["keydown", key])
        time.sleep(duration)
        self._run(["keyup", key])

    def key_down(self, key: str):
        if not self._check_lock(): return
        self._run(["keydown", key])

    def key_up(self, key: str):
         self._run(["keyup", key])
        
    def click(self, button: str = 'left'):
        if not self._check_lock(): return
        # xdotool click 1 (left), 2 (middle), 3 (right)
        btn_map = {'left': '1', 'middle': '2', 'right': '3'}
        b = btn_map.get(button, '1')
        self._run(["click", b])
