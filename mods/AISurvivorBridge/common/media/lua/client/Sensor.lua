-- Sensor.lua
-- Handles scanning the environment around the player with FOV checks.
-- Optimized to use global lists for dynamic entities.

local Sensor = {}
local TAG = "[AISurvivorBridge-Sensor] "

print(TAG .. "Loading...")

local function getSquare(x, y, z)
    local cell = getCell()
    if not cell then return nil end
    return cell:getGridSquare(x, y, z)
end

-- Used for immediate neighbor (3x3) checks
-- Keep detecting zombies here for immediate danger sensing in the 3x3 grid
local function getObjectDataForNeighbor(sq)
    local objs = sq:getObjects()
    local data = {}
    if objs then
        for i=0, objs:size()-1 do
            local obj = objs:get(i)
            local info = nil
            
            if instanceof(obj, "IsoZombie") then 
                info = { type="Zombie" }
            elseif instanceof(obj, "IsoPlayer") then 
                -- info = { type="Player" } 
            elseif instanceof(obj, "IsoWindow") then
                info = { type="Window", open=obj:getSprite():getName():contains("open") }
            elseif instanceof(obj, "IsoDoor") then
                info = { type="Door", open=obj:IsOpen() }
            elseif instanceof(obj, "IsoThumpable") then
                info = { type="Thumpable", name=obj:getName() }
            elseif instanceof(obj, "IsoContainer") then
                info = { type="Container", name=obj:getName() }
            elseif obj:getContainer() then
                info = { type="Container", name=obj:getContainer():getType() }
            end

            if info then
                table.insert(data, info)
            end
        end
    end
    return data
end

-- Extract Zombie Data
local function getZombieInfo(zombie, player)
    local meta = {}
    local dx = zombie:getX() - player:getX()
    local dy = zombie:getY() - player:getY()
    meta.dist = math.sqrt(dx*dx + dy*dy)
    
    local zState = "IDLE"
    local target = zombie:getTarget()
    
    if zombie:isCrawling() then
        zState = "CRAWLING"
    elseif zombie:getHitReaction() ~= "" then
        zState = "STAGGERING" 
    elseif target == player then
        zState = "CHASING"
    elseif target then
        zState = "ALERTED"
    elseif zombie:isMoving() then
        zState = "WANDER"
    end
    
    if zState == "CHASING" and meta.dist < 1.0 then
        zState = "ATTACKING"
    end

    meta.state = zState
    return {
        id = tostring(zombie:getID()),
        type = "Zombie",
        x = math.floor(zombie:getX()),
        y = math.floor(zombie:getY()),
        z = math.floor(zombie:getZ()),
        meta = meta
    }
end

-- Scan radius around player
-- gridRadius: Used for expensive tile/static object scanning (default 10-15)
-- Zombies are scanned with a fixed long-range radius (50)
function Sensor.scan(player, gridRadius)
    local ZOMBIE_RADIUS = 50.0

    local vision = {
        scan_radius = gridRadius,
        timestamp = getTimestampMs(),
        tiles = {},   
        objects = {},
        neighbors = {} 
    }

    if not player then return vision end
    
    local px = math.floor(player:getX())
    local py = math.floor(player:getY())
    local pz = math.floor(player:getZ())
    local playerIndex = player:getPlayerNum()

    -- 1. NEIGHBORS (Immediate 3x3)
    local dirs = {
        n = {0, -1}, s = {0, 1}, e = {1, 0}, w = {-1, 0},
        ne = {1, -1}, nw = {-1, -1}, se = {1, 1}, sw = {-1, 1}
    }
    
    for dir, off in pairs(dirs) do
        local nx, ny = px + off[1], py + off[2]
        local sq = getSquare(nx, ny, pz)
        local status = "blocked" -- default
        local details = {}

        if sq then
            if sq:isFree(false) then status = "walkable" end
            details = getObjectDataForNeighbor(sq)
            
            for _, obj in ipairs(details) do
                if obj.type == "Door" and not obj.open then status = "door_closed" end
                if obj.type == "Window" and not obj.open then status = "window_closed" end
                if obj.type == "Zombie" then status = "danger" end
            end
        end
        
        vision.neighbors[dir] = {
            x = nx, y = ny,
            status = status,
            objects = details
        }
    end

    -- 2. DYNAMIC OBJECT SCAN (Global List)
    -- 2. DYNAMIC OBJECT SCAN (Global List)
    local zombies = getCell():getZombieList()
    local zCount = 0
    vision.debug_z = { total = -1, scan_log = "" }

    if zombies then
        vision.debug_z.total = zombies:size()
        local log_str = ""

        for i=0, zombies:size()-1 do
            local z = zombies:get(i)
            -- Correct logic: Trust instanceof for method existence
            if z and instanceof(z, "IsoZombie") then
                local dx = z:getX() - player:getX()
                local dy = z:getY() - player:getY()
                local dist = math.sqrt(dx*dx + dy*dy)
                
                if dist <= ZOMBIE_RADIUS then
                    local zSq = z:getCurrentSquare()
                    local seen = zSq and zSq:isSeen(playerIndex)
                    
                    -- Debug first few
                    if i < 3 then 
                         log_str = log_str .. string.format("[ID:%d D:%.1f S:%s] ", z:getID(), dist, tostring(seen))
                    end

                    if seen then
                        table.insert(vision.objects, getZombieInfo(z, player))
                        zCount = zCount + 1
                    end
                end
            end
        end
        vision.debug_z.scan_log = log_str
    end
    print(TAG .. "Scan: Global=" .. (zombies and zombies:size() or 0) .. " Visible=" .. zCount)

    -- 3. STATIC GRID SCAN (Tiles & Static Objects)
    -- Iterate grid for map data and static objects (Windows, Doors)
    local startX = px - gridRadius
    local endX   = px + gridRadius
    local startY = py - gridRadius
    local endY   = py + gridRadius

    for x = startX, endX do
        for y = startY, endY do
            local sq = getSquare(x, y, pz)
            if sq and sq:isSeen(playerIndex) then
                -- Tile Info
                local isWalkable = sq:isFree(false)
                if isWalkable then
                     local tileData = { x = x, y = y, z = pz }
                     
                     -- Room Logic
                     local room = sq:getRoom()
                     if room then
                         tileData.room = room:getName()
                     end
                     
                     table.insert(vision.tiles, tileData)
                end

                -- Static Object Info
                -- Skip zombies here as we already got them
                local rawObjs = sq:getObjects()
                if rawObjs then
                    for i=0, rawObjs:size()-1 do
                        local obj = rawObjs:get(i)
                        local objType = nil
                        local meta = {}

                        -- Only check static interactive objects
                        if instanceof(obj, "IsoWindow") then
                            objType = "Window"
                            meta.open = obj:getSprite() and obj:getSprite():getName() and string.find(tostring(obj:getSprite():getName()), "open")
                        elseif instanceof(obj, "IsoDoor") then
                            objType = "Door"
                            meta.open = obj:IsOpen()
                        elseif obj:getContainer() then
                            -- Only verify it's not on a zombie/player (which shouldn't happen in GetObjects normally for the container, but IsZombie checks cover it)
                            -- Actually IsoZombie extends IsoMovingObject.
                            -- We just ensure we don't double count if we only care about static containers
                            if not instanceof(obj, "IsoMovingObject") then
                                objType = "Container"
                                meta.cat = obj:getContainer():getType()
                            end
                        end
                        -- TODO: Add IsoThumpable or other world objects if needed

                        if objType then
                            table.insert(vision.objects, {
                                id = x .. "_" .. y .. "_" .. i,
                                type = objType,
                                x = x, y = y, z = pz,
                                meta = meta
                            })
                        end
                    end
                end
            end
        end
    end

    -- print(TAG .. "Scan Complete. Objects: " .. #vision.objects .. " | Tiles: " .. #vision.tiles)
    return vision
end

print(TAG .. "Loaded.")
return Sensor
