import argparse
import subprocess
import sys
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
PZ_BOT_ROOT = os.path.dirname(os.path.abspath(__file__))
# dev_tools is in the parent directory of pzbot
LAUNCH_SCRIPT = os.path.abspath(os.path.join(PZ_BOT_ROOT, "..", "dev_tools", "launch_pz.bat"))
BOT_RUNTIME_MODULE = "bot_runtime.main"

class BotRestarter(FileSystemEventHandler):
    def __init__(self, start_callback):
        self.start_callback = start_callback
        self.last_restart = time.time()

    def on_any_event(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".py"):
            return
            
        # Debounce
        if time.time() - self.last_restart < 1.0:
            return
            
        print(f"\n[Lifecycle] Change detected in {event.src_path}. Restarting Bot...")
        self.last_restart = time.time()
        self.start_callback()

def run_game(mode="continue", ip=None):
    """Launches the game using the existing batch script."""
    print(f"[Lifecycle] Launching Game in mode: {mode}...")
    
    args = [LAUNCH_SCRIPT]
    if mode == "new":
        args.append("--new")
    elif mode == "continue":
        args.append("--continue")
    elif mode == "join" and ip:
         # PZ Command line args for joining
         # Note: configure_launch.py might try to intercept --join unless we handle it
         # But launch_pz.bat passes %* to BOTH configure_launch and ProjectZomboid64.
         # We need to make sure configure_launch doesn't crash on foreign args, 
         # OR we rely on ProjectZomboid ignoring the config args.
         # Let's pass the direct PZ args:
         args.append(f"-ip {ip}")
         args.append("-port 16261") # Default port
         # We also need to tell configure_launch NOT to overwrite launch_config.json with 'new_game' or 'continue'
         # so we pass nothing special for it? Or we need a updated mode?
         # configure_launch uses parse_args.
         # Let's assume configure_launch gracefully ignores -ip.

    # We use Popen so we don't block
    # Note: args list with spaces needs care in Popen list vs shell=True string
    # Since shell=True, we should join them.
    
    # Platform Check for Linux (Docker)
    is_linux_docker = sys.platform == "linux" and os.path.exists("/root/Zomboid/projectzomboid.sh")
    
    if is_linux_docker:
        print("[Lifecycle] Linux Docker Environment Detected.")
        script_path = "/root/Zomboid/projectzomboid.sh"
        
        # 0. Potato Mode & Auto-Terms
        # Write tuned options.ini to /root/Zomboid/options.ini
        # 0. Potato Mode & Auto-Terms
        # Write tuned options.ini to /root/Zomboid/options.ini
        options_path = "/root/Zomboid/options.ini"
        print(f"[Lifecycle] Injecting 'Potato Mode' options to {options_path}")
        with open(options_path, "w") as f:
            f.write("version=7\n")
            f.write("width=1280\n")
            f.write("height=720\n")
            f.write("fullScreen=false\n")
            f.write("frameRate=30\n")
            f.write("lighting=0\n")
            f.write("lightFPS=15\n")
            f.write("perfSkybox=1\n")
            f.write("perfPuddles=0\n")
            f.write("bPerfReflections=false\n")
            f.write("vidMem=3\n")
            f.write("water=0\n")
            f.write("puddles=0\n")
            f.write("bloodDecals=0\n")
            f.write("textureCompression=true\n")
            f.write("modelTextureMipmaps=false\n")
            f.write("texture2x=false\n")
            f.write("maxTextureSize=1\n")
            
            # EULA Bypass
            f.write("termsOfServiceVersion=100\n") 
            f.write("tutorialDone=true\n")
        
        # 1. Handle Config (Simulate configure_launch.py)
        # We need to tell AutoLoader.lua what to do via launch_config.json
        # Expected Check: /root/Zomboid/Lua/AISurvivorBridge/launch_config.json
        config_dir = "/root/Zomboid/Lua/AISurvivorBridge"
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "launch_config.json")
        
        launch_mode = "continue"
        if mode == "new":
            launch_mode = "new_game"
        elif mode == "join":
            launch_mode = "join" # Not fully supported by Lua yet but consistent
            
        print(f"[Lifecycle] Writing launch config '{launch_mode}' to {config_path}")
        with open(config_path, "w") as f:
            f.write(f'{{"mode": "{launch_mode}"}}')
            
        # 2. Prepare Command
        # projectzomboid.sh usually sets up LD_LIBRARY_PATH and runs Java.
        # We just execute it.
        # It doesn't take --new/--continue args typically, as that's usually for the Lua.
        cmd_str = f"bash {script_path} -nosteam"
        if mode == "join" and ip:
             cmd_str += f" -ip {ip} -port 16261"
             
        # Add some recommended java args if needed, or rely on script defaults.
        # We also usually want -adminpassword for bots if setting up a server, 
        # but for client bot, just running the script is best.
        
    elif sys.platform == "linux" and LAUNCH_SCRIPT.endswith(".bat"):
        # Fallback for Wine (Development on Linux Host, not Docker Hive)
        args.insert(0, "/c")
        args.insert(0, "cmd")
        args.insert(0, "wine")
        print("[Lifecycle] Linux detected for .bat script. Using Wine wrapper.")
        cmd_str = " ".join(args)
    else:
        # Windows Hook (Standard)
        cmd_str = " ".join(args)

    print(f"[Lifecycle] Executing: {cmd_str}")
    subprocess.Popen(cmd_str, cwd=os.path.dirname(script_path) if is_linux_docker else PZ_BOT_ROOT, shell=True)

def run_bot(process_holder):
    """Starts the bot runtime as a subprocess."""
    if process_holder['proc']:
        print("[Lifecycle] Stopping existing bot process...")
        process_holder['proc'].terminate()
        try:
            process_holder['proc'].wait(timeout=5)
        except subprocess.TimeoutExpired:
            process_holder['proc'].kill()
    
    print("[Lifecycle] Starting Bot Runtime...")
    # Run as module to ensure imports work
    process_holder['proc'] = subprocess.Popen(
        [sys.executable, "-m", BOT_RUNTIME_MODULE],
        cwd=PZ_BOT_ROOT
    )

def main():
    parser = argparse.ArgumentParser(description="PZ Bot Lifecycle Manager")
    parser.add_argument("--new", action="store_true", help="Start a new game")
    parser.add_argument("--continue_game", action="store_true", dest="cont", help="Continue latest save")
    parser.add_argument("--dev", action="store_true", help="Enable hot-reloading of bot runtime")
    parser.add_argument("--join", help="IP address to join")

    args = parser.parse_args()

    # 1. Launch Game
    if args.new:
        run_game("new")
    elif args.cont:
        run_game("continue")
    elif args.join:
        run_game("join", ip=args.join)
    
    # 2. Start Bot Runtime
    proc_holder = {'proc': None}
    run_bot(proc_holder)

    # 3. Watchdog (if dev)
    if args.dev:
        print("[Lifecycle] Dev Mode Enabled. Watching for patterns...")
        event_handler = BotRestarter(lambda: run_bot(proc_holder))
        observer = Observer()
        # Watch bot_runtime directory
        watch_path = os.path.join(PZ_BOT_ROOT, "bot_runtime")
        observer.schedule(event_handler, watch_path, recursive=True)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        # Just wait for bot to finish
        try:
            if proc_holder['proc']:
                proc_holder['proc'].wait()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
