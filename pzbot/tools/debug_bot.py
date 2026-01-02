import http.server
import socketserver
import webbrowser
import json
import os
import time

PORT = 8000
# The directory containing the static files
WEB_DIR = os.path.join(os.path.dirname(__file__), 'web')

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'

        # Special Data Endpoint
        if self.path == '/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response_data = {
                "timestamp": time.time(),
                "state_data": {},
                "grid_data": {}
            }
            
            try:
                # 1. Read State (Lua Output)
                # Attempt to find Zomboid root relative to this script
                zomboid_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
                # Path 1: Active Play (Lua dir)
                state_path = os.path.join(zomboid_root, 'Lua/AISurvivorBridge/state.json')
                
                # Path 2: Dev Environment (Mods dir)
                if not os.path.exists(state_path):
                     state_path = os.path.join(zomboid_root, 'mods/AISurvivorBridge/common/state.json')
                     
                if os.path.exists(state_path):
                    for _ in range(5): # Retry loop for file contention
                        try:
                            with open(state_path, 'r') as f:
                                response_data["state_data"] = json.load(f)
                            break
                        except:
                            time.sleep(0.05)
                
                # 2. Read Grid Memory (Python Bot Output)
                grid_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'grid_snapshot.json'))
                if os.path.exists(grid_path):
                    try:
                        with open(grid_path, 'r') as f:
                            response_data["grid_data"] = json.load(f)
                    except:
                        pass

            except Exception as e:
                response_data["error"] = str(e)

            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return
            
        # Serve Static Files (CSS, JS, HTML) via parent class
        return super().do_GET()

    def do_POST(self):
        if self.path == '/control':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                print(f"Received Control: {data}")
                
                # Write to shared control file
                zomboid_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
                control_path = os.path.join(zomboid_root, 'pzbot/config/runtime_control.json')
                
                # Write atomically
                with open(control_path, 'w') as f:
                    json.dump(data, f)
                    
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            except Exception as e:
                print(f"Control Error: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    print(f"Starting Debug Bot on http://localhost:{PORT}")
    print(f"Serving UI from {WEB_DIR}")
    
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        webbrowser.open(f"http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
