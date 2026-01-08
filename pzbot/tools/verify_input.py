import time
import argparse
import sys
import os

# Ensure we can import from bot_runtime
sys.path.append(os.getcwd())

from bot_runtime.input.service import InputService

def run_calisthenics():
    """
    Runs a set of physical movements to verify InputService.
    """
    print("[Verify] Initializing Input Service...")
    input_svc = InputService.get_provider()
    
    print("[Verify] Starting Calisthenics in 3 seconds... FOCUS GAME WINDOW NOW!")
    time.sleep(3)
    
    # 1. WASD Movement
    print("[Verify] 1. Walking Forward (W) for 2s")
    input_svc.hold('w', 2.0)
    time.sleep(0.5)
    
    print("[Verify] 2. Walking Backward (S) for 2s")
    input_svc.hold('s', 2.0)
    time.sleep(0.5)
    
    print("[Verify] 3. Strafing Left (A) for 1s")
    input_svc.hold('a', 1.0)
    
    print("[Verify] 4. Strafing Right (D) for 1s")
    input_svc.hold('d', 1.0)
    
    # 2. Modifiers
    print("[Verify] 5. Sneaking (Toggle C)")
    input_svc.press('c')
    input_svc.hold('w', 1.0) # Sneak forward
    input_svc.press('c') # Untoggle
    
    # 3. Mouse / Combat
    print("[Verify] 6. Aiming (Hold RMB) + Rotate")
    # This requires mouse control logic which we need to verify is in InputService
    # For now, just hold RMB
    # input_svc.mouse_down('right')
    # time.sleep(1.0)
    # input_svc.mouse_up('right')
    
    print("[Verify] 7. Attack (Click LMB)")
    input_svc.click('left')
    time.sleep(0.5)
    input_svc.click('left')
    
    print("[Verify] Calisthenics Complete.")

if __name__ == "__main__":
    run_calisthenics()
