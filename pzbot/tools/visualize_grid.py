
import os
import sys
import json
import webbrowser

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from bot_runtime.world.grid import SpatialGrid, GridTile

import time

def generate_html_map(grid: SpatialGrid, output_path=None, world_items=None, nearby_containers=None):
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "map_view.html")
    
    world_items = world_items or []
    nearby_containers = nearby_containers or []
        
    """
    Generates a self-contained HTML file to visualize the grid.
    """
    # Collect unique rooms/layers for legend
    unique_rooms = set()
    unique_layers = set()
    bounds = {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0} # Default empty bounds
    
    tiles_out = []
    if grid:
        for coord, tile in grid._grid.items():
            t_out = {
                "x": tile.x,
                "y": tile.y,
                "z": tile.z,
                "val": 1,
                "room": getattr(tile, "room", None),
                "layer": getattr(tile, "layer", None)
            }
            tiles_out.append(t_out)
            
            if t_out["room"]:
                unique_rooms.add(t_out["room"])
            if t_out["layer"]:
                unique_layers.add(t_out["layer"])
    
    # Generate Legend HTML dynamically
    legend_html = ''
    
    # Layer Legend (Priority)
    if "Street" in unique_layers: legend_html += '<div class="legend-item"><div class="box" style="background: #555"></div> Street</div>'
    if "Vegetation" in unique_layers: legend_html += '<div class="legend-item"><div class="box" style="background: #2E7D32"></div> Vegetation</div>'
    if "Tree" in unique_layers: legend_html += '<div class="legend-item"><div class="box" style="background: #1B5E20"></div> Tree</div>'
    if "FenceHigh" in unique_layers: legend_html += '<div class="legend-item"><div class="box" style="background: #FF9800"></div> High Fence</div>'
    if "FenceLow" in unique_layers: legend_html += '<div class="legend-item"><div class="box" style="background: #00BCD4; color: #333"></div> Low Fence</div>'
    if "Wall" in unique_layers: legend_html += '<div class="legend-item"><div class="box" style="background: #B71C1C"></div> Wall</div>'
    if "Floor" in unique_layers: legend_html += '<div class="legend-item"><div class="box" style="background: #795548"></div> Floor</div>'
    
    # Default
    legend_html += '<div class="legend-item"><div class="box" style="background: #4CAF50"></div> Default</div>'
    legend_html += '<div class="legend-item"><div class="box" style="background: #FFD700; border-radius: 50%"></div> Container</div>'
    legend_html += '<div class="legend-item"><div class="box" style="background: #00FFFF; border-radius: 50%; width: 6px; height: 6px;"></div> Item</div>'

    # We need to replicate the JS color hashing in Python to generate the correct legend colors
    def string_to_color(s):
        h = 0
        for char in s:
            h = ord(char) + ((h << 5) - h)
        
        color = '#'
        for i in range(3):
            val = (h >> (i * 8)) & 0xFF
            val = min(255, val + 50) # Brighten
            color += f"{val:02x}"
        return color

    for room in sorted(list(unique_rooms)):
        color = string_to_color(room)
        legend_html += f'<div class="legend-item"><div class="box" style="background: {color}"></div> {room}</div>'

    json_data = json.dumps(tiles_out)
    json_items = json.dumps(world_items)
    json_containers = json.dumps(nearby_containers)
    json_bounds = json.dumps(bounds)

    # Prepare HTML template (NOT an f-string to avoid brace escaping issues)
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>PZBot Map Visualizer</title>
    <style>
        body { background: #111; color: #eee; font-family: 'Segoe UI', sans-serif; display: flex; flex-direction: column; align-items: center; margin: 0; padding: 20px; }
        h1 { margin: 0 0 10px 0; }
        canvas { border: 1px solid #444; background: #222; image-rendering: pixelated; }
        #container { display: flex; gap: 20px; align-items: flex-start; }
        #mapColumn { display: flex; flex-direction: column; align-items: center; }
        #sidebar { width: 300px; background: #222; padding: 15px; border-radius: 8px; border: 1px solid #444; max-height: 80vh; overflow-y: auto; }
        #info { margin: 10px; font-size: 0.9em; color: #aaa; }
        .legend { display: flex; gap: 8px; margin: 5px; font-size: 0.8em; flex-wrap: wrap; justify-content: center; max-width: 800px; }
        .legend-item { display: flex; align-items: center; gap: 5px; background: #333; padding: 3px 8px; border-radius: 4px; }
        .box { width: 12px; height: 12px; border: 1px solid rgba(255,255,255,0.2); }
        
        h2 { font-size: 1.1em; border-bottom: 1px solid #444; padding-bottom: 5px; margin-top: 0; }
        ul { list-style: none; padding: 0; margin: 0; }
        li { padding: 8px; border-bottom: 1px solid #333; font-size: 0.9em; }
        li:last-child { border-bottom: none; }
        .item-count { float: right; color: #aaa; font-size: 0.8em; }
        .container-header { font-weight: bold; color: #FFD700; margin-bottom: 4px; display: flex; justify-content: space-between; }
        .item-row { display: flex; justify-content: space-between; color: #ccc; }
        .world-item { color: #00FFFF; }
        
        /* Ghost Styling */
        .ghost { opacity: 0.5; filter: grayscale(100%); }
        .ghost-label { font-size: 0.7em; color: #666; font-style: italic; margin-left: 5px; }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #222; }
        ::-webkit-scrollbar-thumb { background: #444; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #555; }
    </style>
</head>
<body>
    <h1>World Map & Resources</h1>
    
    <div id="container">
        <div id="mapColumn">
            <div id="info">Waiting for data...</div>
            <div id="status" style="font-size: 0.8em; color: #888; margin-bottom: 5px;">Live Updating...</div>
            <canvas id="mapCanvas"></canvas>
            <div class="legend" id="legendContainer">
                <!-- Static Legend Items -->
                <div class="legend-item"><div class="box" style="background: #555"></div> Street</div>
                <div class="legend-item"><div class="box" style="background: #2E7D32"></div> Vegetation</div>
                <div class="legend-item"><div class="box" style="background: #1B5E20"></div> Tree</div>
                <div class="legend-item"><div class="box" style="background: #FF9800"></div> High Fence</div>
                <div class="legend-item"><div class="box" style="background: #00BCD4; color: #333"></div> Low Fence</div>
                <div class="legend-item"><div class="box" style="background: #B71C1C"></div> Wall</div>
                <div class="legend-item"><div class="box" style="background: #795548"></div> Floor</div>
                <div class="legend-item"><div class="box" style="background: #4CAF50"></div> Default</div>
                <div class="legend-item"><div class="box" style="background: #FFD700; border-radius: 50%"></div> Container</div>
                <div class="legend-item"><div class="box" style="background: #00FFFF; border-radius: 50%; width: 6px; height: 6px;"></div> Item</div>
            </div>
        </div>
        
        <div id="sidebar">
            <h2>Nearby Containers (<span id="containerCount">0</span>)</h2>
            <ul id="containerList"></ul>
            
            <h2 style="margin-top: 20px;">World Items (<span id="itemCount">0</span>)</h2>
            <ul id="worldItemList"></ul>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('mapCanvas');
        const ctx = canvas.getContext('2d');
        const TILE_SIZE = 12;
        const PADDING = 20;
        
        let lastUpdate = 0;

        function stringToColor(str) {
            let hash = 0;
            for (let i = 0; i < str.length; i++) {
                hash = str.charCodeAt(i) + ((hash << 5) - hash);
            }
            let color = '#';
            for (let i = 0; i < 3; i++) {
                let value = (hash >> (i * 8)) & 0xFF;
                value = Math.min(255, value + 50); 
                color += ('00' + value.toString(16)).substr(-2);
            }
            return color;
        }

        async function fetchData() {
            try {
                // Fetch header to check if modified
                const response = await fetch('grid_data.json', { cache: "no-cache" });
                if (!response.ok) throw new Error("Network response was not ok");
                
                const data = await response.json();
                
                if (data.timestamp <= lastUpdate) return; // Skip if old data
                lastUpdate = data.timestamp;

                render(data);
                
            } catch (error) {
                console.error("Fetch error:", error);
            }
        }

        function render(data) {
            const tiles = data.tiles;
            const items = data.items;
            const containers = data.containers;
            const bounds = data.bounds;

            // Resize Canvas
            const width = (bounds.max_x - bounds.min_x + 1) * TILE_SIZE + (PADDING * 2);
            const height = (bounds.max_y - bounds.min_y + 1) * TILE_SIZE + (PADDING * 2);
            
            if (canvas.width !== width || canvas.height !== height) {
                canvas.width = width;
                canvas.height = height;
            }
            
            // Update Info
            document.getElementById('info').textContent = `Tiles: ${tiles.length} | Bounds: ${bounds.min_x},${bounds.min_y} to ${bounds.max_x},${bounds.max_y}`;
            document.getElementById('containerCount').textContent = containers.length;
            document.getElementById('itemCount').textContent = items.length;

            // --- RENDER SIDEBAR ---
            const cList = document.getElementById('containerList');
            cList.innerHTML = '';
            if (containers.length === 0) {
                cList.innerHTML = '<li style="color: #666; font-style: italic;">No containers in reach</li>';
            } else {
                containers.forEach(c => {
                    const li = document.createElement('li');
                    const isVisible = c.is_visible !== false;
                    if (!isVisible) li.className = 'ghost';
                    
                    let itemsHtml = (c.items && c.items.length > 0) 
                        ? c.items.map(it => `<div class="item-row"><span>${it.name}</span><span class="item-count">x${it.count}</span></div>`).join('') 
                        : '<div style="color: #666; font-size: 0.8em;">Empty</div>';
                    
                    const ghostLabel = isVisible ? '' : '<span class="ghost-label">(Memory)</span>';
                    li.innerHTML = `
                        <div class="container-header">
                            <span>${c.object_type || "Unknown Container"}${ghostLabel}</span>
                            <span style="font-weight: normal; font-size: 0.8em; color: #888;">${c.items ? c.items.length : 0} items</span>
                        </div>
                        <div style="padding-left: 5px;">${itemsHtml}</div>
                    `;
                    cList.appendChild(li);
                });
            }

            const wList = document.getElementById('worldItemList');
            wList.innerHTML = '';
            if (items.length === 0) {
                wList.innerHTML = '<li style="color: #666; font-style: italic;">No items on ground</li>';
            } else {
                items.forEach(it => {
                    const li = document.createElement('li');
                    const isVisible = it.is_visible !== false;
                    li.className = isVisible ? 'world-item' : 'world-item ghost';
                    const ghostLabel = isVisible ? '' : '<span class="ghost-label">(Memory)</span>';
                    li.innerHTML = `
                        <div class="item-row" style="color: ${isVisible ? '#00FFFF' : '#888'};">
                            <span>${it.name}${ghostLabel}</span>
                            <span style="font-size: 0.8em; color: #aaa;">(${it.x}, ${it.y})</span>
                        </div>
                        <div style="font-size: 0.7em; color: #666;">${it.category || 'Unknown'}</div>
                    `;
                    wList.appendChild(li);
                });
            }
            
            // --- DRAW CANVAS ---
            ctx.clearRect(0, 0, width, height);
            ctx.fillStyle = "rgba(30, 30, 30, 0.95)";
            ctx.fillRect(0, 0, width, height);

            function toCanvas(x, y) {
                return {
                    x: (x - bounds.min_x) * TILE_SIZE + PADDING,
                    y: (y - bounds.min_y) * TILE_SIZE + PADDING
                };
            }

            // Draw Tiles
            tiles.forEach(t => {
                const pos = toCanvas(t.x, t.y);
                
                if (t.room && t.room !== "outside") ctx.fillStyle = stringToColor(t.room);
                else if (t.layer === "Tree") ctx.fillStyle = "#1B5E20";
                else if (t.layer === "Vegetation") ctx.fillStyle = "#2E7D32";
                else if (t.layer === "Street") ctx.fillStyle = "#555";
                else if (t.layer === "Floor") ctx.fillStyle = "#795548";
                else if (t.layer === "FenceHigh") ctx.fillStyle = "#FF9800";
                else if (t.layer === "FenceLow") ctx.fillStyle = "#00BCD4";
                else if (t.layer === "Wall") ctx.fillStyle = "#B71C1C";
                else ctx.fillStyle = "#4CAF50";
                
                ctx.fillRect(pos.x, pos.y, TILE_SIZE - 1, TILE_SIZE - 1);
            });

            // Draw Containers
            containers.forEach(c => {
                const pos = toCanvas(c.x, c.y);
                const isVisible = c.is_visible !== false;
                
                ctx.fillStyle = isVisible ? "#FFD700" : "#666666";
                if (!isVisible) ctx.strokeStyle = "#444";
                
                ctx.beginPath();
                ctx.arc(pos.x + TILE_SIZE/2, pos.y + TILE_SIZE/2, TILE_SIZE/3, 0, 2 * Math.PI);
                ctx.fill();
                ctx.strokeStyle = "black";
                ctx.lineWidth = 1;
                ctx.stroke();
            });

            // Draw Items
            items.forEach(it => {
                const pos = toCanvas(it.x, it.y);
                const isVisible = it.is_visible !== false;
                ctx.fillStyle = isVisible ? "#00FFFF" : "#558888";
                ctx.beginPath();
                ctx.arc(pos.x + TILE_SIZE/2 + 2, pos.y + TILE_SIZE/2 + 2, TILE_SIZE/5, 0, 2 * Math.PI);
                ctx.fill();
            });
        }

        // Poll every 500ms
        setInterval(fetchData, 500);
        fetchData();
    </script>
</body>
</html>
    """
    
    with open(output_path, "w") as f:
        f.write(html_template)
    
    return os.path.abspath(output_path)

def write_data_json(tiles_out, world_items, nearby_containers, bounds, output_dir):
    data = {
        "timestamp": time.time(),
        "bounds": bounds,
        "tiles": tiles_out,
        "items": world_items,
        "containers": nearby_containers
    }
    
    output_path = os.path.join(output_dir, "grid_data.json")
    # Atomic write pattern: write to temp, rename
    temp_path = output_path + ".tmp"
    with open(temp_path, "w") as f:
        json.dump(data, f)
    os.replace(temp_path, output_path)

import http.server
import socketserver
import threading

def start_server(directory, port=8000):
    """Starts a simple HTTP server in a daemon thread."""
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)
        
        # Suppress log messages for clean output
        def log_message(self, format, *args):
            pass

    def run():
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"Serving at http://localhost:{port}")
            httpd.serve_forever()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return port

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    snapshot_path = os.path.join(base_dir, "grid_snapshot.json")
    html_path = os.path.join(base_dir, "map_view.html")
    
    # Generate HTML once
    print(f"Generating viewer at {html_path}...")
    generate_html_map(None, output_path=html_path)
    
    # Start Server
    port = start_server(base_dir, port=8000)
    
    # Open Browser via HTTP
    webbrowser.open(f"http://localhost:{port}/map_view.html")
    print("Browser opened. Monitoring for updates...")

    last_mtime = 0.0
    
    try:
        while True:
            if os.path.exists(snapshot_path):
                try:
                    current_mtime = os.stat(snapshot_path).st_mtime
                    
                    if current_mtime > last_mtime:
                        last_mtime = current_mtime
                        
                        with open(snapshot_path, "r") as f:
                            data = json.load(f)
                            
                        # Extract Data
                        world_items = data.get("world_items", [])
                        nearby_containers = data.get("nearby_containers", [])
                        tile_data_raw = data.get("tiles", [])
                        
                        # Calculate Bounds
                        if not tile_data_raw:
                            bounds = {"min_x": 0, "max_x": 100, "min_y": 0, "max_y": 100}
                        else:
                            xs = [t["x"] for t in tile_data_raw]
                            ys = [t["y"] for t in tile_data_raw]
                            bounds = {
                                "min_x": min(xs),
                                "max_x": max(xs),
                                "min_y": min(ys),
                                "max_y": max(ys),
                            }
                        
                        # Just pass raw tile data for JSON (optimize later if needed)
                        tiles_out = tile_data_raw 

                        write_data_json(tiles_out, world_items, nearby_containers, bounds, base_dir)
                        
                except json.JSONDecodeError:
                    # Partial read or empty file (race condition), skip frame silently
                    pass
                except Exception as e:
                    print(f"Error processing snapshot: {e}")
                    # Don't crash loop
                    time.sleep(1)
            else:
                 pass
                
            time.sleep(0.1) # Fast poll for file changes
            
    except KeyboardInterrupt:
        print("\nStopped monitoring.")
