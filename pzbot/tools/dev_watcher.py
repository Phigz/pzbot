import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pathlib

class RestartHandler(FileSystemEventHandler):
    def __init__(self, command):
        self.command = command
        self.process = None
        self.restart()

    def restart(self):
        if self.process:
            print("Changes detected. Restarting bot...")
            self.process.terminate()
            self.process.wait()
        
        print(f"Starting bot: {' '.join(self.command)}")
        self.process = subprocess.Popen(self.command)

    def on_any_event(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.py') or event.src_path.endswith('.yaml'):
             # Debounce or simple restart
             # Ideally we debounce but for now simple restart is fine
             # (Watchdog events can be spammy, so real implementation might need a small delay)
             self.restart()

if __name__ == "__main__":
    target_dir = sys.argv[1]
    command = sys.argv[2:]
    
    print(f"Watching {target_dir} for changes...")
    
    event_handler = RestartHandler(command)
    observer = Observer()
    observer.schedule(event_handler, target_dir, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    observer.join()
