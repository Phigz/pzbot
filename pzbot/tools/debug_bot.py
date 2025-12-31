import http.server
import socketserver
import webbrowser
import json
import os
import time

PORT = 8000
HTML_FILE = 'debug_view.html'

html = """<!DOCTYPE html>
<html>
<head>
    <title>PZBot Debugger</title>
    <style>
        :root { --bg: #111; --panel: #1e1e1e; --border: #333; --text: #eee; --text-dim: #888; --accent: #4CAF50; --warn: #FF9800; --danger: #f44336; }
        body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', monospace; margin: 0; padding: 0; display: flex; height: 100vh; overflow: hidden; }
        
        /* Layout */
        #main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
        #sidebar { width: 400px; background: var(--panel); border-left: 1px solid var(--border); display: flex; flex-direction: column; flex-shrink: 0; }
        
        /* Header */
        header { padding: 4px 15px; background: #181818; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; height: 40px; }
        h1 { margin: 0; font-size: 1.0em; color: var(--accent); font-weight: 600; }
        #status { font-size: 0.75em; color: var(--text-dim); }

        /* Map Area */
        #mapContainer { flex: 1; position: relative; overflow: hidden; background: #050505; }
        canvas { display: block; image-rendering: pixelated; }

        /* Sidebar Panels */
        .tabs { display: flex; border-bottom: 1px solid var(--border); background: #222; flex-shrink: 0; }
        .tab { flex: 1; padding: 10px; text-align: center; cursor: pointer; color: var(--text-dim); font-size: 0.9em; transition: 0.2s; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .tab:hover { background: #2a2a2a; color: #fff; }
        .tab.active { border-bottom: 2px solid var(--accent); color: #fff; background: var(--panel); }

        .content-pane { flex: 1; overflow-y: auto; display: none; padding: 10px; min-height: 0; }
        .content-pane.active { display: block; }
        
        .section { margin-bottom: 15px; background: #252525; border-radius: 4px; padding: 10px; border: 1px solid #333; }
        .section h2 { margin-top: 0; font-size: 0.9em; color: #ccc; border-bottom: 1px solid #444; padding-bottom: 5px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        
        .row { display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 0.85em; }
        .label { color: var(--text-dim); }
        .val { color: #fff; font-weight: bold; }
        
        /* Colors */
        .stat-bar { height: 4px; background: #333; border-radius: 2px; margin-top: 2px; overflow: hidden; }
        .stat-fill { height: 100%; background: var(--accent); transition: width 0.3s; }
        .tag { display: inline-block; padding: 2px 6px; border-radius: 3px; background: #333; font-size: 0.75em; margin-right: 4px; margin-bottom: 4px; }
        .tag.bad { background: #5a1a1a; color: #ffadad; border: 1px solid #8d2d2d; }
        .tag.good { background: #1a3a1a; color: #adffad; border: 1px solid #2d5d2d; }
        .item-row { padding: 4px; border-bottom: 1px solid #333; font-size: 0.8em; }

        .legend { position: absolute; bottom: 10px; left: 10px; background: rgba(0,0,0,0.85); padding: 10px; border-radius: 4px; font-size: 0.75em; pointer-events: none; border: 1px solid #444; display: flex; gap: 20px; z-index: 10; }
        .legend-section { display: flex; flex-direction: column; gap: 2px; }
        .legend-title { font-weight: bold; color: #aaa; margin-bottom: 4px; border-bottom: 1px solid #444; padding-bottom: 2px; white-space: nowrap; }
        .legend-item { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; color: #ccc; }
        .box { width: 12px; height: 12px; }
        .circle { border-radius: 50%; }
        
        pre { font-size: 0.7em; color: #aaa; white-space: pre-wrap; word-break: break-all; }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #111; }
        ::-webkit-scrollbar-thumb { background: #444; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #555; }
    </style>
</head>
<body>
    <div id="main">
        <header>
            <h1>PZBot Debugger</h1>
            <div id="status">Waiting...</div>
        </header>
        <div id="mapContainer">
            <canvas id="mapCanvas"></canvas>
            <div class="legend" id="legend"></div>
        </div>
    </div>

    <div id="sidebar">
        <div class="tabs">
            <div class="tab active" onclick="switchTab('player')">Player</div>
            <div class="tab" onclick="switchTab('entities')">Live</div>
            <div class="tab" onclick="switchTab('memory')">Memory</div>
            <div class="tab" onclick="switchTab('raw')">Raw</div>
        </div>

        <div id="player" class="content-pane active">
            <div class="section"><h2>Vitals</h2><div id="vitalsContainer">Waiting...</div></div>
            <div class="section"><h2>State</h2><div id="stateContainer">Waiting...</div></div>
            <div class="section"><h2>Moodles</h2><div id="moodlesContainer">Waiting...</div></div>
            <div class="section"><h2>Inventory</h2><div id="inventoryContainer">Waiting...</div></div>
        </div>

        <div id="entities" class="content-pane">
            <div class="section"><h2>Zombies (<span id="zombieCount">0</span>)</h2><div id="zombieList"></div></div>
            <div class="section"><h2>Containers (<span id="containerCount">0</span>)</h2><div id="containerList"></div></div>
            <div class="section"><h2>Vehicles (<span id="vehCount">0</span>)</h2><div id="vehList"></div></div>
        </div>
        
        <div id="memory" class="content-pane">
            <div class="section"><h2>Zombies (<span id="memZombieCount">0</span>)</h2><div id="memZombieList"></div></div>
            <div class="section"><h2>Containers (<span id="memContainerCount">0</span>)</h2><div id="memContainerList"></div></div>
             <div class="section"><h2>Vehicles (<span id="memVehCount">0</span>)</h2><div id="memVehList"></div></div>
        </div>

        <div id="raw" class="content-pane">
             <div class="section"><h2>Full State JSON</h2><pre id="rawJson">No Data</pre></div>
        </div>
    </div>

    <script>
        function switchTab(id) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.content-pane').forEach(p => p.classList.remove('active'));
            document.querySelector(`.tab[onclick="switchTab('${id}')"]`).classList.add('active');
            document.getElementById(id).classList.add('active');
        }

        
        const mapContainer = document.getElementById('mapContainer');
        const canvas = document.getElementById('mapCanvas');
        const ctx = canvas.getContext('2d');
        const TILE_SIZE = 14;

        // Double Buffering
        const offscreenCanvas = document.createElement('canvas');
        const offCtx = offscreenCanvas.getContext('2d');
        
        // Colors (Brightened)
        const COLORS = {
            Tree: '#2E7D32', Vegetation: '#1b3b1b', Street: '#444', Floor: '#3a3a3a', 
            FenceHigh: '#a0522d', FenceLow: '#cd853f', Wall: '#888', Default: '#111',
            Window: '#aaa', Door: '#4fc',
            ZombieLive: '#ff4444', ZombieMem: '#ff8888', 
            ContainerLive: '#ffff00', ContainerMem: '#cccc00',
            ItemLive: '#00ffff', ItemMem: '#00aaaa',
            VehicleLive: '#2196F3', VehicleMem: '#1565C0', Player: '#4CAF50'
        };

        function getStringColor(t) {
            // Priority: Room hash -> Layer -> Default
            if (t.room && t.room !== "outside") return stringToHashColor(t.room); 
            return COLORS[t.layer] || COLORS.Default;
        }

        function stringToHashColor(str) {
            let hash = 0;
            for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
            let color = '#';
            for (let i = 0; i < 3; i++) {
                let val = (hash >> (i * 8)) & 0xFF;
                val = Math.min(150, val + 40);
                color += ('00' + val.toString(16)).substr(-2);
            }
            return color;
        }

        function getHealthColor(h) {
             if (h < 0.3) return '#f44336'; if (h < 0.7) return '#FF9800'; return '#4CAF50';
        }
        
        const asArray = (x) => Array.isArray(x) ? x : [];
        
        const getTTL = (o) => {
             if (o.ttl_remaining_ms) {
                 const s = Math.ceil(o.ttl_remaining_ms / 1000);
                 if (s > 86400) return ''; // Hide infinite/long TTL
                 let c = '#4CAF50';
                 if(s < 10) c='#f44336'; else if(s < 60) c='#FF9800';
                 return `<span class="tag" style="color:${c}; border-color:${c}33; background:${c}11">TTL:${s}s</span>`;
             }
             return '';
        }

        // Helper: Render Container Contents
        // Used for World Containers, Vehicle Parts, and Player Inventory
        function renderContainer(c, label, color, headerSuffix) {
            // c can be a Container object (with .items) or a Vehicle Part (with .container.items or similar)
            // c can also be a simple Inventory Item (with .items if it's a bag, or just properties)
            
            let items = null;
            let cap = "";
            let suffix = headerSuffix || "";
            let extraInfo = "";
            
            const isContainer = (c.items !== undefined) || (c.container && c.container.items);
            
            // 1. Standard Container or simple Item list
            if (c.items) items = asArray(c.items);
            // 2. Vehicle Part often has 'container' sub-object
            else if (c.container && c.container.items) items = asArray(c.container.items);
            
            // Format items
            let contentHtml = "";
            
            if (items && items.length > 0) {
                 // Recursive Render
                 contentHtml = items.map(i => renderContainer(i, i.name || i.type, color)).join('');
            } else if (isContainer) {
                 contentHtml = '<span style="color:#666; font-style:italic; margin-left:10px;">Empty</span>';
            }
            
            // Item Logic (TTL, Coords)
            extraInfo += getTTL(c);
            
            // Append Coordinates if present and NOT a top-level container (which usually passes coords in label/headerSuffix)
            // Top level containers usually have coords in label passed by updateMemory. items don't.
            if (c.x !== undefined && c.y !== undefined && !headerSuffix) {
                suffix += ` <span style="color:#666; font-size:0.8em;">(${c.x},${c.y})</span>`;
            }
            
            // Specialized Item Info (Condition, etc.) if available
            // Assuming this is passed in `c`
            // Durability Display Logic
            // 1. Must have condition value
            // 2. Must be damageable (according to new Lua export)
            // 3. EXCLUDE known non-damageable categories like Keys, Literature, Container (unless special?)
            //    Check 'cat' field.
            
            // NOTE: Clothing technically has condition (holes) but maybe user doesn't want bars for socks.
            // User specifically mentioned KeyRing and ID Card. ID Card is likely Literature or Key?
            // Let's filter strictly.
            
            let showDurability = false;
            if (c.cond !== undefined && c.isDamageable) {
                showDurability = true;
                if (c.cat && (c.cat === 'Key' || c.cat === 'Literature')) showDurability = false;
                // Specific override for "Key Ring" if category is ambiguous
                if (c.name && c.name.includes("Key Ring")) showDurability = false;
            }

            if (showDurability) {
                 const w = (c.cond * 100).toFixed(0);
                 const col = getHealthColor(c.cond);
                 extraInfo += `<div class="stat-bar" style="width:50px; display:inline-block; margin-left:5px;"><div class="stat-fill" style="width:${w}%; background:${col}"></div></div>`;
            }

            // Weapon Stats
            if (c.minDmg !== undefined) {
                 const min = c.minDmg.toFixed(1);
                 const max = c.maxDmg ? c.maxDmg.toFixed(1) : "?";
                 const crit = c.crit ? c.crit.toFixed(0) : "0";
                 extraInfo += `<span style="font-size:0.8em; color:#aaa; margin-left:5px;">Dmg: ${min}-${max} | Crit: ${crit}%</span>`;
            }
                
            // If it's not a container and has no contents, hiding the content div entirely is cleaner
            const showContent = (items && items.length > 0) || (items && isContainer);
            
            // Append ID if available (checking top level c.id)
            let idSpan = "";
            if (c.id) {
                 idSpan = `<span style="color:#555; font-size:0.75em; margin-left:4px;">[#${c.id}]</span>`;
            }

            return `<div class="item-row" style="color:${color}">
                <strong>${label}</strong>${idSpan} ${extraInfo} ${cap} ${suffix}
                ${showContent ? `<div style="margin-left:10px; margin-top:2px;">${contentHtml}</div>` : ''}
            </div>`;
        }

        async function poll() {
            try {
                const res = await fetch('/data');
                const data = await res.json();
                if (data.error) document.getElementById('status').innerText = "Backend Error: " + data.error;
                
                if (data.state_data) {
                    const lat = (Date.now() / 1000) - data.timestamp;
                    document.getElementById('status').innerText = `Tick: ${data.state_data.tick || 0} | Latency: ${lat.toFixed(3)}s`;
                    updatePlayer(data.state_data.player);
                    updateEntities(data.state_data);
                    updateRaw(data.state_data);
                }
                if (data.grid_data) {
                    updateMemory(data.grid_data);
                    renderMap(data.grid_data, data.state_data);
                }
            } catch (e) {
                console.error(e);
            }
        }

        function updatePlayer(p) { if(!p) return; 
             // ... Simple Vital Update ...
             const h = p.body ? p.body.health/100 : 0;
             document.getElementById('vitalsContainer').innerHTML = 
                `<div class="row">Health: ${(h*100).toFixed(0)}%</div><div class="stat-bar"><div class="stat-fill" style="width:${h*100}%; background:${getHealthColor(h)}"></div></div>`;
             
             // ... State ...
             document.getElementById('stateContainer').innerHTML = `X:${p.position.x.toFixed(1)} Y:${p.position.y.toFixed(1)}`;

             // ... Moodles ...
             const moodles = asArray(p.moodles);
             if (moodles.length > 0) {
                 document.getElementById('moodlesContainer').innerHTML = moodles.map(m => {
                     // 1=Good, 2=Bad, 0=Neutral (Approximation)
                     let bg = '#333';
                     let border = '#444';
                     if (m.sentiment === 1) { bg = '#1a3a1a'; border = '#2d5d2d'; } // Good (Greenish)
                     else if (m.sentiment === 2 || m.sentiment === 4) { bg = '#5a1a1a'; border = '#8d2d2d'; } // Bad (Redish)
                     
                     // Visualize Level (1-4)
                     const pips = "I".repeat(m.value || 1);
                     
                     return `<div class="tag" style="background:${bg}; border:1px solid ${border}">${m.name} <span style="opacity:0.6">${pips}</span></div>`
                 }).join('');
             } else {
                 document.getElementById('moodlesContainer').innerHTML = '<span style="color:#666">Calm</span>';
             }

             // ... Inventory ...
             const inv = asArray(p.inventory);
             if (inv.length > 0) {
                 document.getElementById('inventoryContainer').innerHTML = inv.map(i => 
                     renderContainer(i, i.name, '#eee', `<span style="font-size:0.8em; color:#888;">x${i.count||1}</span>`)
                 ).join('');
             } else {
                 document.getElementById('inventoryContainer').innerHTML = '<span style="color:#666">Empty</span>';
             }
        }

        function updateEntities(state) { 
             // 1. Zombies
             const v = state.player?.vision || {};
             const zombies = asArray(v.objects).filter(x=>x.type=='Zombie');
             document.getElementById('zombieCount').innerText = zombies.length;
             document.getElementById('zombieList').innerHTML = zombies.map(z => 
                `<div class="item-row" style="color:${COLORS.ZombieLive}">Zombie #${z.id} (${z.x.toFixed(1)},${z.y.toFixed(1)})</div>`
             ).join('');

             // 2. Containers
             const containers = asArray(v.nearby_containers);
             document.getElementById('containerCount').innerText = containers.length;
             document.getElementById('containerList').innerHTML = containers.map(c => {
                 // Ensure ID is available for renderContainer if stored in meta
                 if (!c.id && c.meta && c.meta.parent_id) c.id = c.meta.parent_id;
                 return renderContainer(c, `${c.object_type} (${c.x},${c.y})`, COLORS.ContainerLive);
             }).join('');

             // 3. Vehicles
             const vehicles = asArray(v.vehicles);
             document.getElementById('vehCount').innerText = vehicles.length;
             document.getElementById('vehList').innerHTML = vehicles.map(v => {
                // Break down parts
                const partsWithContainer = asArray(v.parts).filter(p => p.container || p.items); 
                let partsHtml = "";
                if (partsWithContainer.length > 0) {
                     partsHtml = partsWithContainer.map(p => {
                         const pName = p.id || p.name || "Part";
                         // Parts have IDs already? Yes, usually part name.
                         return renderContainer(p, pName, "#ccc");
                     }).join('');
                } else {
                     partsHtml = `<div style="margin-left:10px; color:#666;">No accessible containers</div>`;
                }
                
                // Vehicle ID Logic
                let vId = v.id || "??";
                vId = vId.replace("vehicle_", "");

                return `<div class="item-row" style="border-left: 2px solid ${COLORS.VehicleLive}; padding-left:8px;">
                    <div style="color:${COLORS.VehicleLive}; font-weight:bold;">${v.object_type || 'Unknown'} [#${vId}] (${v.x.toFixed(1)},${v.y.toFixed(1)})</div>
                    ${partsHtml}
                </div>`;
             }).join('');
             
             // 4. Items - Removed as requested
             // document.getElementById('itemCount').innerText = ...
             // document.getElementById('itemList').innerHTML = ...
        }

        function updateMemory(g) {
             const getTTL = (o) => {
                 if (o.ttl_remaining_ms) {
                     const s = Math.ceil(o.ttl_remaining_ms / 1000);
                     let c = '#4CAF50';
                     if(s < 10) c='#f44336'; else if(s < 60) c='#FF9800';
                     return `<span class="tag" style="color:${c}; border-color:${c}33; background:${c}11">TTL:${s}s</span>`;
                 }
                 return '';
             }

             // 1. Zombies
             const zombies = asArray(g.zombies);
             document.getElementById('memZombieCount').innerText = zombies.length;
             document.getElementById('memZombieList').innerHTML = zombies.map(z => 
                `<div class="item-row" style="color:${COLORS.ZombieMem}">Zombie #${z.id} (${z.x},${z.y}) ${getTTL(z)}</div>`
             ).join('');

             // 2. Containers
             const containers = asArray(g.nearby_containers);
             document.getElementById('memContainerCount').innerText = containers.length;
             document.getElementById('memContainerList').innerHTML = containers.map(c => {
                 if (!c.id && c.meta && c.meta.parent_id) c.id = c.meta.parent_id;
                 return renderContainer(c, `${c.object_type} (${c.x},${c.y})`, COLORS.ContainerMem);
             }).join('');

             // 3. Vehicles
             const vehicles = asArray(g.vehicles);
             document.getElementById('memVehCount').innerText = vehicles.length;
             document.getElementById('memVehList').innerHTML = vehicles.map(v => {
                 // Check if memory has full parts or just simplified
                 const parts = asArray(v.parts || (v.properties ? v.properties.parts : []));
                 const partsWithContainer = parts.filter(p => p.container || p.items);
                 let partsHtml = "";
                 
                 if (partsWithContainer.length > 0) {
                     partsHtml = partsWithContainer.map(p => {
                         const pName = p.id || p.name || "Part";
                         return renderContainer(p, pName, "#888");
                     }).join('');
                 } else {
                     partsHtml = `<div style="margin-left:10px; color:#555;">No container info</div>`;
                 }
                 
                 let vId = v.id || "??";
                 vId = vId.replace("vehicle_", "");

                return `<div class="item-row" style="border-left: 2px solid ${COLORS.VehicleMem}; padding-left:8px;">
                    <div style="color:${COLORS.VehicleMem}; font-weight:bold;">${v.object_type || 'Unknown'} [#${vId}] (${v.x.toFixed(1)},${v.y.toFixed(1)}) ${getTTL(v)}</div>
                    ${partsHtml}
                </div>`;
             }).join('');
        }

        function updateRaw(s) { document.getElementById('rawJson').innerText = JSON.stringify(s, null, 2); }

        function renderMap(grid, state) {
            if (!grid || !grid.tiles) return;

            // Resize Helper
            const w = mapContainer.clientWidth;
            const h = mapContainer.clientHeight;
            
            // Resize Offscreen
            if (offscreenCanvas.width !== w || offscreenCanvas.height !== h) {
                offscreenCanvas.width = w; offscreenCanvas.height = h;
            }
            // Resize Onscreen
            if (canvas.width !== w || canvas.height !== h) {
                canvas.width = w; canvas.height = h;
            }

            // Draw to Offscreen --------------------------------------
            offCtx.fillStyle = "#000"; offCtx.fillRect(0, 0, w, h);
            
            let cx = 0, cy = 0;
            const playerPos = state?.player?.position;
            
            if (playerPos) {
                cx = playerPos.x;
                cy = playerPos.y;
            } else {
                 cx = (grid.bounds?.min_x + grid.bounds?.max_x) / 2 || 0;
                 cy = (grid.bounds?.min_y + grid.bounds?.max_y) / 2 || 0;
            }

            const toScreen = (wx, wy) => ({
                x: Math.floor((wx - cx) * TILE_SIZE + w/2),
                y: Math.floor((wy - cy) * TILE_SIZE + h/2)
            });

            // 1. Tiles
            const viewRadX = (w / TILE_SIZE) / 2 + 5;
            const viewRadY = (h / TILE_SIZE) / 2 + 5;

            grid.tiles.forEach(t => {
                if (Math.abs(t.x - cx) > viewRadX || Math.abs(t.y - cy) > viewRadY) return;
                const pos = toScreen(t.x, t.y);
                offCtx.fillStyle = getStringColor(t);
                offCtx.fillRect(pos.x, pos.y, TILE_SIZE, TILE_SIZE);
            });

            // Helper for Offscreen
            const draw = (x, y, col, shape, filled) => {
                const pos = toScreen(x, y);
                if (pos.x < -20 || pos.y < -20 || pos.x > w+20 || pos.y > h+20) return;
                
                offCtx.fillStyle = col; offCtx.strokeStyle = col;
                const sz = TILE_SIZE * 0.8;
                const off = (TILE_SIZE - sz)/2;
                
                if (shape == 'rect') {
                    if (filled) offCtx.fillRect(pos.x+off, pos.y+off, sz, sz);
                    else offCtx.strokeRect(pos.x+off, pos.y+off, sz, sz);
                } else {
                    offCtx.beginPath();
                    offCtx.arc(pos.x + TILE_SIZE/2, pos.y + TILE_SIZE/2, sz/2, 0, 6.28);
                    if (filled) offCtx.fill(); else offCtx.stroke();
                }
            };

            // 2. Memory
            asArray(grid.vehicles).forEach(v => draw(v.x, v.y, COLORS.VehicleMem, 'rect', false));
            asArray(grid.zombies).forEach(z => draw(z.x, z.y, COLORS.ZombieMem, 'circle', false));
            asArray(grid.nearby_containers).forEach(c => draw(c.x, c.y, COLORS.ContainerMem, 'rect', false));

            // 3. Live
            if (state?.player?.vision) {
                const v = state.player.vision;
                asArray(v.vehicles).forEach(veh => draw(veh.x, veh.y, COLORS.VehicleLive, 'rect', true));
                asArray(v.objects).filter(o=>o.type=='Zombie').forEach(z => draw(z.x, z.y, COLORS.ZombieLive, 'circle', true));
                
                // Player
                if (playerPos) draw(playerPos.x, playerPos.y, COLORS.Player, 'circle', true);
            }

            // Flip Buffer
            ctx.drawImage(offscreenCanvas, 0, 0);

            // Legend
             let legendHtml = '';
            const TILE_KEYS = ['Tree', 'Vegetation', 'Street', 'Floor', 'Wall', 'FenceHigh', 'FenceLow', 'Window', 'Door'];
            legendHtml += `<div class="legend-section"><div class="legend-title">Tiles</div>`;
            legendHtml += TILE_KEYS.map(k => `<div class="legend-item"><div class="box" style="background: ${COLORS[k] || COLORS.Default}"></div> ${k}</div>`).join('');
            legendHtml += `</div><div class="legend-section"><div class="legend-title">Entities</div>`;
            legendHtml += `<div class="legend-item"><div class="box" style="background: ${COLORS.VehicleLive}"></div> Vehicle</div>`;
            legendHtml += `<div class="legend-item"><div class="box circle" style="background: ${COLORS.ZombieLive}"></div> Zombie</div>`;
            legendHtml += `<div class="legend-item"><div class="box" style="background: ${COLORS.ContainerLive}"></div> Container</div>`;
            legendHtml += `<div class="legend-item"><div class="box" style="background: ${COLORS.ItemLive}"></div> Item</div>`;
            legendHtml += `<div class="legend-item"><div class="box circle" style="background: ${COLORS.Player}"></div> Player</div>`;
            legendHtml += `</div>`;
            document.getElementById('legend').innerHTML = legendHtml;
        }

        let lastState = null;
        let lastGrid = null;

        async function poll() {
            try {
                const res = await fetch('/data');
                const data = await res.json();
                if (data.error) document.getElementById('status').innerText = "Backend Error: " + data.error;
                
                if (data.state_data) {
                    lastState = data.state_data;
                    const lat = (Date.now() / 1000) - data.timestamp;
                    document.getElementById('status').innerText = `Tick: ${lastState.tick || 0} | Latency: ${lat.toFixed(3)}s`;
                    updatePlayer(lastState.player);
                    updateEntities(lastState);
                    updateRaw(lastState);
                }
                if (data.grid_data && data.grid_data.tiles && data.grid_data.tiles.length > 0) {
                    // Only update grid if we got valid tiles
                    lastGrid = data.grid_data;
                    updateMemory(lastGrid);
                }
            } catch (e) {
                console.error(e);
            }
            setTimeout(poll, 700); // Reschedule
        }

        function animate() {
            if (lastGrid && lastState) {
                 renderMap(lastGrid, lastState);
            }
            requestAnimationFrame(animate);
        }

        // Start Loops
        poll();
        requestAnimationFrame(animate);
    </script>
</body>
</html>
"""

def update_html():
    with open(HTML_FILE, 'w') as f:
        f.write(html)
    return HTML_FILE

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/debug_view.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open(HTML_FILE, 'rb') as f:
                self.wfile.write(f.read())
            return

        if self.path == '/data':
            # Handle data request safely
            response_data = {
                "timestamp": time.time(),
                "state_data": {},
                "grid_data": {}
            }
            
            try:
                # Read State
                # Check standard Lua output location first (Zomboid/Lua/...)
                # Assuming script is running from Zomboid/pzbot/tools
                # Path to Zomboid root is ../.. (pzbot/tools -> pzbot -> Zomboid)
                zomboid_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
                state_path = os.path.join(zomboid_root, 'Lua/AISurvivorBridge/state.json')
                
                # Fallback to mod source if not found
                if not os.path.exists(state_path):
                     state_path = os.path.join(zomboid_root, 'mods/AISurvivorBridge/common/state.json')

                if os.path.exists(state_path):
                    # Robust Read with retries
                    for _ in range(5):
                        try:
                            with open(state_path, 'r') as f:
                                response_data["state_data"] = json.load(f)
                            break
                        except:
                            time.sleep(0.05)
                
                # Read Grid Snapshot
                grid_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'grid_snapshot.json'))
                if os.path.exists(grid_path):
                    try:
                        with open(grid_path, 'r') as f:
                            response_data["grid_data"] = json.load(f)
                    except:
                        pass # Ignore grid errors for now
            
            except Exception as e:
                response_data["error"] = str(e)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return
            
        return super().do_GET()

if __name__ == '__main__':
    update_html()
    print(f"Starting Debug Bot on http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        webbrowser.open(f"http://localhost:{PORT}")
        httpd.serve_forever()
