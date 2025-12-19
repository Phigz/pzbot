
import os
import sys
import json
import webbrowser

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from bot_runtime.world.grid import SpatialGrid, GridTile

import time

# ... (imports)

def generate_html_map(grid: SpatialGrid, output_path=None):
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "map_view.html")
        
    """
    Generates a self-contained HTML file to visualize the grid.
    """
    # ... (serialization logic same as before)
    tiles_data = []
    for coord, tile in grid._grid.items():
        tiles_data.append({
            "x": tile.x,
            "y": tile.y,
            "z": tile.z,
            "val": 1 # Walkable
        })
    
    # Calculate bounds dynamically from actual tiles to avoid outliers/ghost data
    if not tiles_data:
        bounds = {"min_x": 0, "max_x": 100, "min_y": 0, "max_y": 100}
    else:
        xs = [t["x"] for t in tiles_data]
        ys = [t["y"] for t in tiles_data]
        bounds = {
            "min_x": min(xs),
            "max_x": max(xs),
            "min_y": min(ys),
            "max_y": max(ys),
        }

    json_data = json.dumps(tiles_data)
    json_bounds = json.dumps(bounds)

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>PZBot Map Visualizer</title>
    <!-- Auto-refresh every 3 seconds -->
    <meta http-equiv="refresh" content="3">
    <style>
        body {{ background: #1a1a1a; color: #eee; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; }}
        canvas {{ border: 1px solid #444; background: #000; image-rendering: pixelated; }}
        #info {{ margin: 10px; }}
    </style>
</head>
<body>
    <h1>World Map</h1>
    <div id="info">Tiles: {len(tiles_data)} | Bounds: {bounds['min_x']},{bounds['min_y']} to {bounds['max_x']},{bounds['max_y']}</div>
    <div id="status" style="font-size: 0.8em; color: #888;">Live Updating...</div>
    <canvas id="mapCanvas"></canvas>
    <script>
        const tiles = {json_data};
        const bounds = {json_bounds};
        
        const canvas = document.getElementById('mapCanvas');
        const ctx = canvas.getContext('2d');
        
        const TILE_SIZE = 5;
        const PADDING = 20;
        
        const width = (bounds.max_x - bounds.min_x + 1) * TILE_SIZE + (PADDING * 2);
        const height = (bounds.max_y - bounds.min_y + 1) * TILE_SIZE + (PADDING * 2);
        
        canvas.width = width;
        canvas.height = height;
        
        function draw() {{
            ctx.fillStyle = "#000";
            ctx.fillRect(0, 0, width, height);
            
            ctx.fillStyle = "#4CAF50"; // Green for walkable
            
            tiles.forEach(t => {{
                // Transform world coords to canvas coords
                const cx = (t.x - bounds.min_x) * TILE_SIZE + PADDING;
                const cy = (t.y - bounds.min_y) * TILE_SIZE + PADDING;
                
                ctx.fillRect(cx, cy, TILE_SIZE - 1, TILE_SIZE - 1);
            }});
        }}
        
        draw();
    </script>
</body>
</html>
    """
    
    with open(output_path, "w") as f:
        f.write(html_content)
    
    return os.path.abspath(output_path)

if __name__ == "__main__":
    # Snapshot is now in the same directory as this script
    snapshot_path = os.path.join(os.path.dirname(__file__), "grid_snapshot.json")
    last_mtime = 0.0
    browser_opened = False
    
    print(f"Monitoring {snapshot_path} for updates...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            if os.path.exists(snapshot_path):
                current_mtime = os.stat(snapshot_path).st_mtime
                
                if current_mtime > last_mtime:
                    print(f"Update detected at {time.ctime(current_mtime)}")
                    last_mtime = current_mtime
                    
                    try:
                        with open(snapshot_path, "r") as f:
                            data = json.load(f)
                            
                        grid = SpatialGrid()
                        # Reconstruct grid
                        for t_data in data["tiles"]:
                            key = (t_data['x'], t_data['y'], t_data['z'])
                            grid._grid[key] = GridTile(**t_data)
                            
                        # Calculate bounds dynamically
                        if not data.get("tiles"):
                            bounds = {"min_x": 0, "max_x": 100, "min_y": 0, "max_y": 100}
                        else:
                            # Re-calculate from loaded data just to be safe
                            xs = [t["x"] for t in data["tiles"]]
                            ys = [t["y"] for t in data["tiles"]]
                            bounds = {
                                "min_x": min(xs),
                                "max_x": max(xs),
                                "min_y": min(ys),
                                "max_y": max(ys),
                            }
                        
                        grid.min_x = bounds["min_x"]
                        grid.max_x = bounds["max_x"]
                        grid.min_y = bounds["min_y"]
                        grid.max_y = bounds["max_y"]
                        
                        path = generate_html_map(grid)
                        print(f"Map updated: {path}")
                        
                        if not browser_opened:
                            webbrowser.open(f"file://{path}")
                            browser_opened = True
                            
                    except Exception as e:
                        print(f"Error processing snapshot: {e}")
                        import traceback
                        traceback.print_exc()
            else:
                if not browser_opened:
                    print("Waiting for snapshot file...")
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopped monitoring.")
