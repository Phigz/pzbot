import pydirectinput
import time
import sys

def test_input():
    print("!!! PREPARE TO SWITCH TO GAME WINDOW !!!")
    print("You have 5 seconds to focus the Project Zomboid window...")
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("Testing 'W' key (Walk Forward)...")
    pydirectinput.keyDown('w')
    time.sleep(1.0)
    pydirectinput.keyUp('w')
    
    time.sleep(0.5)
    
    print("Testing 'Space' key (Shove)...")
    pydirectinput.press('space')
    
    print("Test complete.")

if __name__ == "__main__":
    test_input()
