import os
import time
import ctypes
from ctypes import wintypes

# Konstants for Windows API
User32 = ctypes.windll.user32
SW_RESTORE = 9

# Virtual Key Codes
VK_SPACE = 0x20
VK_RETURN = 0x0D
VK_LBUTTON = 0x01

# Input structures for SendInput
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_ulonglong)]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_ulonglong)]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [("type", wintypes.DWORD),
                ("_input", _INPUT)]

LPINPUT = ctypes.POINTER(INPUT)

def send_key(hexKeyCode):
    # Key Down
    x = INPUT(type=1, ki=KEYBDINPUT(wVk=hexKeyCode))
    User32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
    time.sleep(0.05)
    # Key Up
    x = INPUT(type=1, ki=KEYBDINPUT(wVk=hexKeyCode, dwFlags=0x0002)) # KEYEVENTF_KEYUP
    User32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

def send_click():
    # Move to absolute center of screen (65535 is max dimension for ABSOLUTE coords)
    mi_move = MOUSEINPUT(dx=32768, dy=32768, mouseData=0, dwFlags=0x8001, time=0, dwExtraInfo=0) # MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
    x_move = INPUT(type=0, mi=mi_move)
    User32.SendInput(1, ctypes.byref(x_move), ctypes.sizeof(x_move))
    
    time.sleep(0.1)

    # Mouse Down
    mi_down = MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=0x0002, time=0, dwExtraInfo=0)
    x_down = INPUT(type=0, mi=mi_down)
    User32.SendInput(1, ctypes.byref(x_down), ctypes.sizeof(x_down))
    
    time.sleep(0.1)
    
    # Mouse Up
    mi_up = MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=0x0004, time=0, dwExtraInfo=0)
    x_up = INPUT(type=0, mi=mi_up)
    User32.SendInput(1, ctypes.byref(x_up), ctypes.sizeof(x_up))

def focus_window(title):
    hwnd = User32.FindWindowW(None, title)
    if hwnd:
        User32.ShowWindow(hwnd, SW_RESTORE)
        User32.SetForegroundWindow(hwnd)
        return True
    return False

def main():
    log_path = r"c:\Users\lucas\Zomboid\console.txt"
    target_pattern = "game loading took"
    
    print(f"Monitoring {log_path} for '{target_pattern}'...")
    
    # Wait for file to exist
    while not os.path.exists(log_path):
        time.sleep(1)

    # Monitor file
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        # Start reading from beginning
        # f.seek(0, os.SEEK_END)
        
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            
            if target_pattern in line:
                print(f"Trigger found in line: {line.strip()}")
                print("Game load detected! Waiting 1 seconds before click...")
                time.sleep(1)
                
                print("Attempting to focus 'Project Zomboid' window...")
                window_found = False
                for i in range(10): 
                    if focus_window("Project Zomboid"):
                        window_found = True
                        break
                    print(f"Window not found, retrying... ({i+1}/10)")
                    time.sleep(1)

                if window_found:
                    time.sleep(0.5)
                    
                    print("Clicking...")
                    send_click()
                    
                    print("Input sent. Exiting.")
                    return
                else:
                    print("Could not find window 'Project Zomboid' after retries.")
                    return

if __name__ == "__main__":
    main()
