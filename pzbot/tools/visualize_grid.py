
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
    
    tiles_out = []
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
    <!-- Auto-refresh every 3 seconds -->
    <meta http-equiv="refresh" content="3">
    <style>
        body {{ background: #111; color: #eee; font-family: 'Segoe UI', sans-serif; display: flex; flex-direction: column; align-items: center; margin: 0; padding: 20px; }}
        h1 {{ margin: 0 0 10px 0; }}
        canvas {{ border: 1px solid #444; background: #222; image-rendering: pixelated; }}
        #container {{ display: flex; gap: 20px; align-items: flex-start; }}
        #mapColumn {{ display: flex; flex-direction: column; align-items: center; }}
        #sidebar {{ width: 300px; background: #222; padding: 15px; border-radius: 8px; border: 1px solid #444; max-height: 80vh; overflow-y: auto; }}
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
            <div id="info">Tiles: {{TILE_COUNT}} | Bounds: {{BOUNDS_TEXT}}</div>
            <div class="legend">
                {{LEGEND_HTML}}
            </div>
            <div id="status" style="font-size: 0.8em; color: #888; margin-bottom: 5px;">Live Updating...</div>
            <canvas id="mapCanvas"></canvas>
        </div>
        
        <div id="sidebar">
            <h2>Nearby Containers ({{CONTAINER_COUNT}})</h2>
            <ul id="containerList">
                <!-- Populated by JS -->
            </ul>
            
            <h2 style="margin-top: 20px;">World Items ({{ITEM_COUNT}})</h2>
            <ul id="worldItemList">
                <!-- Populated by JS -->
            </ul>
        </div>
    </div>

    <script>
        const tiles = {{JSON_DATA}};
        const items = {{JSON_ITEMS}};
        const containers = {{JSON_CONTAINERS}};
        const bounds = {{JSON_BOUNDS}};
        
        const canvas = document.getElementById('mapCanvas');
        const ctx = canvas.getContext('2d');
        
        const TILE_SIZE = 12; // Slightly larger
        const PADDING = 20;
        
        const width = (bounds.max_x - bounds.min_x + 1) * TILE_SIZE + (PADDING * 2);
        const height = (bounds.max_y - bounds.min_y + 1) * TILE_SIZE + (PADDING * 2);
        
        canvas.width = width;
        canvas.height = height;
        
        // --- RENDER LISTS ---
        function renderLists() {
            // Containers
            const cList = document.getElementById('containerList');
            cList.innerHTML = ''; // Clear previous list
            if (containers.length === 0) {
                cList.innerHTML = '<li style="color: #666; font-style: italic;">No containers in reach</li>';
            } else {
                containers.forEach(c => {
                    const li = document.createElement('li');
                    const isVisible = c.is_visible !== false; // Default true
                    
                    if (!isVisible) li.className = 'ghost';
                    
                    let itemsHtml = '';
                    if (c.items && c.items.length > 0) {
                        itemsHtml = c.items.map(it => `<div class="item-row"><span>${it.name}</span><span class="item-count">x${it.count}</span></div>`).join('');
                    } else {
                        itemsHtml = '<div style="color: #666; font-size: 0.8em;">Empty</div>';
                    }
                    
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
            
            // World Items
            const wList = document.getElementById('worldItemList');
            wList.innerHTML = ''; // Clear previous list
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
        }

        // Color hashing for consistent room colors - MUST MATCH PYTHON
        function stringToColor(str) {
            let hash = 0;
            for (let i = 0; i < str.length; i++) {
                hash = str.charCodeAt(i) + ((hash << 5) - hash);
            }
            let color = '#';
            for (let i = 0; i < 3; i++) {
                let value = (hash >> (i * 8)) & 0xFF;
                // Brighten semantics to distinguish from dark background
                value = Math.min(255, value + 50); 
                color += ('00' + value.toString(16)).substr(-2);
            }
            return color;
        }
        
        function toCanvas(x, y) {
            return {
                x: (x - bounds.min_x) * TILE_SIZE + PADDING,
                y: (y - bounds.min_y) * TILE_SIZE + PADDING
            };
        }
        
        function draw() {
            ctx.clearRect(0, 0, width, height);
            ctx.fillStyle = "rgba(30, 30, 30, 0.95)";
            ctx.fillRect(0, 0, width, height);
            
            // Draw Tiles
            tiles.forEach(t => {
                // Transform world coords to canvas coords
                const pos = toCanvas(t.x, t.y);
                const cx = pos.x;
                const cy = pos.y;
                
                // Priority: Room > Tree > Layer > Default
                if (t.room) {
                    ctx.fillStyle = stringToColor(t.room);
                } else if (t.layer === "Tree") {
                    ctx.fillStyle = "#1B5E20"; // Dark Forest Green
                } else if (t.layer === "Vegetation") {
                    ctx.fillStyle = "#2E7D32"; // Green
                } else if (t.layer === "Street") {
                    ctx.fillStyle = "#555"; // Asphalt
                } else if (t.layer === "Floor") {
                    ctx.fillStyle = "#795548"; // Brown
                } else if (t.layer === "FenceHigh") {
                    ctx.fillStyle = "#FF9800"; // Orange (High / Climb)
                } else if (t.layer === "FenceLow") {
                    ctx.fillStyle = "#00BCD4"; // Cyan (High Contrast vs Orange)
                } else if (t.layer === "Wall") {
                    ctx.fillStyle = "#B71C1C"; // Red (Solid Wall)
                } else {
                    ctx.fillStyle = "#4CAF50"; // Default Green (Grass/Unknown)
                }
                
                ctx.fillRect(cx, cy, TILE_SIZE - 1, TILE_SIZE - 1);
            });
            
            // Draw Containers
            containers.forEach(c => {
                const pos = toCanvas(c.x, c.y);
                const isVisible = c.is_visible !== false;
                
                ctx.fillStyle = isVisible ? "#FFD700" : "#666666"; // Gold vs Grey
                if (!isVisible) ctx.strokeStyle = "#444";
                
                ctx.beginPath();
                ctx.arc(pos.x + TILE_SIZE/2, pos.y + TILE_SIZE/2, TILE_SIZE/3, 0, 2 * Math.PI);
                ctx.fill();
                ctx.strokeStyle = "black";
                ctx.lineWidth = 1;
                ctx.stroke();
            });
            
            // Draw World Items
            items.forEach(it => {
                const pos = toCanvas(it.x, it.y);
                const isVisible = it.is_visible !== false;
                
                ctx.fillStyle = isVisible ? "#00FFFF" : "#558888"; // Cyan vs Dim Cyan
                
                ctx.beginPath();
                ctx.arc(pos.x + TILE_SIZE/2 + 2, pos.y + TILE_SIZE/2 + 2, TILE_SIZE/5, 0, 2 * Math.PI);
                ctx.fill();
            });
        }
        
        renderLists();
        draw();
    </script>
</body>
</html>
    """
    
    # Inject variables using .replace() for safety
    html_content = html_template.replace("{{TILE_COUNT}}", str(len(tiles_out)))
    html_content = html_content.replace("{{BOUNDS_TEXT}}", f"{bounds['min_x']},{bounds['min_y']} to {bounds['max_x']},{bounds['max_y']}")
    html_content = html_content.replace("{{LEGEND_HTML}}", legend_html)
    html_content = html_content.replace("{{CONTAINER_COUNT}}", str(len(nearby_containers)))
    html_content = html_content.replace("{{ITEM_COUNT}}", str(len(world_items)))
    html_content = html_content.replace("{{JSON_DATA}}", json_data)
    html_content = html_content.replace("{{JSON_ITEMS}}", json_items)
    html_content = html_content.replace("{{JSON_CONTAINERS}}", json_containers)
    html_content = html_content.replace("{{JSON_BOUNDS}}", json_bounds)
    
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
                        
                        # Extract Items & Containers
                        world_items = data.get("world_items", [])
                        nearby_containers = data.get("nearby_containers", [])
                        
                        path = generate_html_map(grid, world_items=world_items, nearby_containers=nearby_containers)
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
