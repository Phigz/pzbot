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

    @classmethod
    def get_provider(cls) -> InputProvider:
        if cls._instance:
            return cls._instance
        
        system = platform.system()
        if system == "Windows":
            cls._instance = WindowsInputProvider()
        elif system == "Linux":
            cls._instance = LinuxInputProvider()
        else:
            print(f"WARNING: Unsupported OS '{system}'. Defaulting to no-op Linux provider.")
            cls._instance = LinuxInputProvider()
            
        return cls._instance
