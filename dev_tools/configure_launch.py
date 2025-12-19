import argparse
import json
import os
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Configure Project Zomboid Bot Launch")
    parser.add_argument('--new', action='store_true', help="Force a new game")
    parser.add_argument('--continue', dest='continue_game', action='store_true', help="Continue the latest save")
    # Allow loose matching for /new style
    
    args, unknown = parser.parse_known_args()
    
    # Simple logic to handle /new passed as unknown or specific flags
    mode = "continue"
    if args.new:
        mode = "new_game"
    
    # Handle manual check for /new or similar in unknowns if argparse didn't catch it
    for arg in unknown:
        if "/new" in arg or "new" in arg:
            mode = "new_game"
    
    config_data = {"mode": mode}
    
    # Target Path: c:\Users\lucas\Zomboid\Lua\AISurvivorBridge\launch_config.json
    # We use the user's home directory dynamically to be safe, or hardcode if preferred strictly for this env.
    # Given the user context: c:\Users\lucas\Zomboid...
    
    user_home = Path(os.path.expanduser("~"))
    zomboid_lua_path = user_home / "Zomboid" / "Lua" / "AISurvivorBridge"
    
    try:
        zomboid_lua_path.mkdir(parents=True, exist_ok=True)
        config_file = zomboid_lua_path / "launch_config.json"
        
        # Read existing config to preserve other settings (like log_level)
        existing_data = {}
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"Warning: Could not read existing config: {e}")

        # Update with new mode
        existing_data.update(config_data)
        
        with open(config_file, 'w') as f:
            json.dump(existing_data, f, indent=4)
            
        print(f"Launch Config Updated: {mode} -> {config_file}")
    except Exception as e:
        print(f"Error writing config: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
