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
-- Extract Generic Actor Data (Zombie, Player, Animal)
local function getActorInfo(actor, player)
    local meta = {}
    local dx = actor:getX() - player:getX()
    local dy = actor:getY() - player:getY()
    meta.dist = math.sqrt(dx*dx + dy*dy)
    
    local typeStr = "Unknown"
    local idStr = tostring(actor:getID())
    
    -- 1. ZOMBIE LOGIC
    if instanceof(actor, "IsoZombie") then
        typeStr = "Zombie"
        local zState = "IDLE"
        local target = actor:getTarget()
        
        if actor:isCrawling() then
            zState = "CRAWLING"
        elseif actor:getHitReaction() ~= "" then
            zState = "STAGGERING" 
        elseif target == player then
            zState = "CHASING"
        elseif target then
            zState = "ALERTED"
        elseif actor:isMoving() then
            zState = "WANDER"
        end
        
        if zState == "CHASING" and meta.dist < 1.0 then
            zState = "ATTACKING"
        end
        meta.state = zState

    -- 2. ANIMAL LOGIC (B42 / Generic) - Prioritized over Player
    elseif instanceof(actor, "IsoAnimal") then
        typeStr = "Animal"
        
        -- Safely extract Breed Name 
        pcall(function() 
            local breedObj = actor:getBreed() 
            if breedObj then
                 if breedObj.getName then meta.breed = breedObj:getName()
                 else meta.breed = tostring(breedObj) end
            end
        end)
        
        -- Extract Species
        pcall(function() if actor.getAnimalType then meta.species = actor:getAnimalType() end end)

        -- PROBES for Enhanced Stats
        -- Gender
        pcall(function() if actor.isFemale then meta.isFemale = actor:isFemale() end end)
        
        -- Age / Days Alive
        pcall(function() if actor.getAge then meta.age = actor:getAge() end end)
        
        -- Health usually on BodyDamage or direct getHealth
        pcall(function() if actor.getHealth then meta.health = actor:getHealth() end end)
        
        -- EXPERIMENTAL: Animal Specific Probes (Based on Wiki)
        pcall(function()
             -- Size
             if actor.getSize then meta.size = actor:getSize() end
             -- Milking
             if actor.isMilking then meta.milking = actor:isMilking() end
             -- Interaction / Taming (Guesses)
             if actor.isPetable then meta.isPetable = actor:isPetable() end
             if actor.canBePet then meta.canBePet = actor:canBePet() end
             if actor.canBeAttached then meta.canBeAttached = actor:canBeAttached() end
             
             -- Stats (Hunger/Thirst) - Check for direct access first
             if actor.getHunger then meta.hunger = actor:getHunger() end
             if actor.getThirst then meta.thirst = actor:getThirst() end
             
             -- Stats Object Check
             if actor.getStats then
                 local stats = actor:getStats()
                 if stats then
                     if stats.getHunger then meta.hunger = stats:getHunger() end
                     if stats.getThirst then meta.thirst = stats:getThirst() end
                 end
             end
        end)
        
        -- 2. Moodles (Standard PZ Needs System)
        pcall(function()
            if actor.getMoodles then
                local moods = actor:getMoodles()
                if moods then
                    -- print("[SENSOR-PROBE] Moodles Object: " .. tostring(moods))
                end
            end
        end)



        -- Debug Print (Can silence later)
        -- print("[SENSOR-PROBE] Animal Stats: Breed="..tostring(meta.breed).." Spp="..tostring(meta.species).." Fem="..tostring(meta.isFemale).." Age="..tostring(meta.age).." Health="..tostring(meta.health))
    
    -- 3. PLAYER LOGIC
    elseif instanceof(actor, "IsoPlayer") then

        -- Debug Print (Can silence later)
        -- print("[SENSOR-PROBE] Animal Stats: Breed="..tostring(meta.breed).." Spp="..tostring(meta.species).." Fem="..tostring(meta.isFemale).." Age="..tostring(meta.age).." Health="..tostring(meta.health))
    
    -- 3. PLAYER LOGIC
    elseif instanceof(actor, "IsoPlayer") then
        typeStr = "Player"
        meta.username = actor:getUsername()
        if actor:isAiming() then meta.state = "AIMING" end
    end
    
    -- GENERIC CHARACTER LOGIC (Zombies + Players) - Worn Items / Weapons
    if typeStr == "Zombie" or typeStr == "Player" then
         -- Weapon Info
         local hand = actor:getPrimaryHandItem()
         if hand then meta.weapon = hand:getDisplayName() end
         
         -- Worn Items (Backpacks / Bags)
         pcall(function() 
             local worn = actor:getWornItems()
             if worn then
                 meta.worn = {}
                 for i=0, worn:size()-1 do
                     local item = worn:getItemByIndex(i)
                     if item then
                         -- Check if it's a container or bag-like
                         -- checking item:IsInventoryContainer() (Java method often exposed as IsInventoryContainer) or category
                         local isBag = false
                         if item.IsInventoryContainer and item:IsInventoryContainer() then isBag = true end
                         if not isBag and string.find(item:getName(), "Bag") then isBag = true end
                         if not isBag and string.find(item:getName(), "Pack") then isBag = true end
                         
                         if isBag then
                             table.insert(meta.worn, item:getDisplayName())
                         end
                     end
                 end
             end
         end)
    end

    return {
        id = idStr,
        type = typeStr,
        x = math.floor(actor:getX()),
        y = math.floor(actor:getY()),
        z = math.floor(actor:getZ()),
        meta = meta
    }
end

-- SIGNAL SENSOR
-- Scans Radio/TV devices for power, channel, and content
local function getSignals(player)
    local signals = {}
    -- Scan radius for signals (hearing range is roughly 10-20 tiles, but let's go 30)
    local SCAN_DIST_SQ = 30 * 30 
    
    if ZomboidRadio then
        local radio = ZomboidRadio.getInstance()
        if radio and radio.getDevices then
            local devices = radio:getDevices()
            if devices then
                for i=0, devices:size()-1 do
                    local dev = devices:get(i)
                    if dev then
                        local dx = dev:getX() - player:getX()
                        local dy = dev:getY() - player:getY()
                        
                        if (dx*dx + dy*dy) <= SCAN_DIST_SQ then
                             local data = nil
                             if dev.getDeviceData then data = dev:getDeviceData() end
                             
                             if data then
                                 local isPower = false
                                 if data.getIsTurnedOn then isPower = data:getIsTurnedOn() end
                                 
                                 local lastMsg = nil
                                 if dev.getSayLine then lastMsg = dev:getSayLine() end
                                 
                                 -- Device Type
                                 local typeName = "Radio"
                                 if dev.getSprite and dev:getSprite() and dev:getSprite():getName() and string.find(dev:getSprite():getName(), "television") then
                                     typeName = "TV"
                                 end
                                 
                                 table.insert(signals, {
                                     x = math.floor(dev:getX()),
                                     y = math.floor(dev:getY()),
                                     z = math.floor(dev:getZ()),
                                     type = typeName,
                                     name = data:getDeviceName() or "Unknown",
                                     on = isPower,
                                     channel = data:getChannel() and data:getChannel() or -1,
                                     volume = data:getDeviceVolume() and data:getDeviceVolume() or 0.0,
                                     msg = lastMsg
                                 })
                             end
                        end
                    end
                end
            end
        end
    end
    
    return signals
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
        neighbors = {},
        -- sounds = {}, -- Removed: LastHeard data is ambiguous (Location only)
        signals = getSignals(player) 
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
    -- 2. DYNAMIC ACTOR SCAN (Global List)
    -- We now scan ALL IsoGameCharacters (Zombies, Players) AND IsoAnimals explicitly
    local allObjects = getCell():getObjectList()
    local zCount = 0 -- Keep var name for compatibility, effectively "Generic Count"
    vision.debug_z = { total = -1, scan_log = "" }

    if allObjects then
        vision.debug_z.total = allObjects:size()
        local log_str = ""

        for i=0, allObjects:size()-1 do
            local obj = allObjects:get(i)
            
            -- Filter: Must be Character OR Animal
            if obj and (instanceof(obj, "IsoGameCharacter") or instanceof(obj, "IsoAnimal")) then
                
                -- SELF CHECK LOGGING
                local isSelf = (obj == player)
                
                if not isSelf then
                    local dx = obj:getX() - player:getX()
                    local dy = obj:getY() - player:getY()
                    local dist = math.sqrt(dx*dx + dy*dy)
                    
                    -- Use ZOMBIE_RADIUS as general "Entity Radius" (50 tiles)
                    if dist <= ZOMBIE_RADIUS then
                        local zSq = obj:getCurrentSquare()
                        local seen = zSq and zSq:isSeen(playerIndex)
                        
                        -- BYPASS: Allow Animals even if not seen (for debugging/tracking)
                        local forceInclude = instanceof(obj, "IsoAnimal")
                        
                        if seen or forceInclude then
                            local info = getActorInfo(obj, player)
                            -- print("[SENSOR-ADD] Adding Entity: Type="..tostring(info.type).." ID="..tostring(info.id).." Class="..tostring(obj:getClass():getSimpleName()))
                            table.insert(vision.objects, info)
                            zCount = zCount + 1
                        else
                             -- DEBUG: Log why Animal wasn't seen
                             if instanceof(obj, "IsoAnimal") then
                                 local sqStr = "nil"
                                 if zSq then sqStr = tostring(zSq:getX())..","..tostring(zSq:getY()) end
                                 print("[SENSOR-SKIP] Animal skipped. ID:"..tostring(obj:getID()).." Dist:"..tostring(dist).." Sq:"..sqStr.." Seen:"..tostring(seen))
                             end
                        end
                    end
                else
                    -- Log self-skipping to double check logic
                    -- print("[SENSOR-SKIP] Skipping Self: " .. tostring(obj:getID()))
                end
            end
        end
        vision.debug_z.scan_log = log_str
    end
    -- print(TAG .. "Scan: Global=" .. (zombies and zombies:size() or 0) .. " Visible=" .. zCount)

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
                -- Always include tile if seen, even if blocked (so we can see Walls/Trees)
                local tileData = { x = x, y = y, z = pz, w = isWalkable }
                     
                -- Room Logic
                local room = sq:getRoom()
                if room then
                    tileData.room = room:getName()
                end

                     -- Semantic Layer Logic (Refactored)
                     local layer = nil
                     
                     -- Classification Rules (Priority Order: Higher index = Lower priority check, but we break on success)
                     -- Actually, we want specific matches to win.
                     -- Let's check objects first (Trees, Walls), then overlays, then Floor.
                     
                     local function classifySprite(sName)
                        if not sName then return nil end
                        
                        -- 1. Trees (Explicitly exclude 'street' to prevent false positives)
                        if (string.find(sName, "tree") and not string.find(sName, "street")) 
                           or string.find(sName, "_american_") or string.find(sName, "_canadian_") then
                            return "Tree"
                        end
                        
                        -- 2. Fences & Walls
                        if string.find(sName, "fencing") or string.find(sName, "walls_interior") then 
                            return "FenceLow"
                        end
                        if string.find(sName, "walls_exterior_house") then return "Wall" end
                        if string.find(sName, "walls_exterior") then return "FenceHigh" end
                        
                        -- 3. Street / Pavement
                        if string.find(sName, "street") then return "Street" end
                        
                        -- 4. Floors (Interior)
                        if string.find(sName, "floors_interior") or string.find(sName, "floors_rugs") then return "Floor" end
                        
                        -- 5. Vegetation (Catch-all)
                        if string.find(sName, "vegetation") or string.find(sName, "blends_natural") or string.find(sName, "grass") then
                            return "Vegetation"
                        end
                        
                        return nil
                     end
                     
                     -- 1. Check Objects (Trees, Fences, etc.)
                     local objs = sq:getObjects()
                     if objs then
                        for i=0, objs:size()-1 do
                            local o = objs:get(i)
                            
                            -- IsoTree override
                            if instanceof(o, "IsoTree") then 
                                layer = "Tree"
                                break 
                            end
                            
                            local sprite = o:getSprite()
                            if sprite and sprite:getName() then
                                local found = classifySprite(tostring(sprite:getName()))
                                if found then
                                    layer = found
                                    -- High priority layers break the loop immediately
                                    if layer == "Tree" or layer == "Wall" or layer == "FenceHigh" then break end
                                end
                            end
                        end
                     end
                     
                     -- 2. Check Floor (if no dominant object layer found yet)
                     if not layer then
                        local floor = sq:getFloor()
                        if floor then
                            local sprite = floor:getSprite()
                            if sprite and sprite:getName() then
                                layer = classifySprite(tostring(sprite:getName()))
                            end
                        end
                     end
                     
                     if layer then
                        tileData.layer = layer
                     end
                     
                     table.insert(vision.tiles, tileData)

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
                        elseif instanceof(obj, "IsoContainer") then
                            -- Only verify it's not on a zombie/player (for safety, though unlikely in static list)
                            if not instanceof(obj, "IsoMovingObject") then
                                objType = "Container"
                                meta.cat = obj:getContainer():getType()
                            end
                        end
                        
                        -- SIGNAL/DEVICE SCAN (Grid Based)
                        if instanceof(obj, "IsoTelevision") or instanceof(obj, "IsoRadio") then
                             local deviceData = nil
                             if obj.getDeviceData then deviceData = obj:getDeviceData() end
                             
                             if deviceData then
                                 local isPower = false
                                 if deviceData.getIsTurnedOn then isPower = deviceData:getIsTurnedOn() end
                                 
                                 local chan = -1
                                 if deviceData.getChannel then chan = deviceData:getChannel() end
                                 
                                 local vol = 0.0
                                 if deviceData.getDeviceVolume then vol = deviceData:getDeviceVolume() end
                                 
                                 local dName = "Unknown"
                                 if deviceData.getDeviceName then dName = deviceData:getDeviceName() end
                                 
                                 -- Media / VHS Check
                                 local mediaTitle = nil
                                 local mediaCat = nil
                                 if deviceData.hasMedia and deviceData:hasMedia() and deviceData.getMediaData then
                                     local media = deviceData:getMediaData()
                                     if media then
                                         if media.getTitle then mediaTitle = media:getTitle() 
                                         elseif media.getName then mediaTitle = media:getName() end
                                         
                                         if media.getCategory then mediaCat = media:getCategory() end
                                     end
                                 end
                                 
                                 local sType = "Radio"
                                 if instanceof(obj, "IsoTelevision") then sType = "TV" end
                                 
                                 local deviceMsg = nil
                                 if mediaTitle then
                                     deviceMsg = "Media: " .. tostring(mediaTitle)
                                     if mediaCat then deviceMsg = deviceMsg .. " (" .. tostring(mediaCat) .. ")" end
                                 end

                                 table.insert(vision.signals, {
                                     x = x,
                                     y = y,
                                     z = pz,
                                     type = sType,
                                     name = dName,
                                     on = isPower,
                                     channel = chan,
                                     volume = vol,
                                     msg = deviceMsg
                                 })
                             end
                        end

                        -- CONTAINER FALLBACK (for objects that have a container but aren't IsoContainer check above)
                        if not objType and obj:getContainer() and not instanceof(obj, "IsoMovingObject") then
                             objType = "Container"
                             meta.cat = obj:getContainer():getType()
                        end

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

    -- Helper for processing items
    -- ID STRATEGY: We force string IDs derived from InventoryItem:getID().
    -- Using WorldObject IDs (wi:getID()) proved unsafe/unstable.
    -- String IDs ensure compatibility with Python's JSON parser (preventing #unknown_0_0 issues).
    local function processSensorItem(item)
        local id = tostring(item:getID())
        
        -- Removed risky WorldID check which caused crashes/ambiguity
        
         -- 0-1 Normalized Condition
        local cond = 0
        if item.getConditionMax and item.getCondition then
            local max = item:getConditionMax()
            if max > 0 then cond = item:getCondition() / max end
        end
        
        local isDamageable = false
        if item.isDamageable then isDamageable = item:isDamageable() end
        
        local d = {
            id = id,
            type = item:getFullType(),
            name = item:getName(),
            cat = tostring(item:getCategory()),
            weight = item:getActualWeight(),
            cond = cond,
            isDamageable = isDamageable,
            count = 1
        }
        
        if instanceof(item, "HandWeapon") then
             d.minDmg = item:getMinDamage()
             d.maxDmg = item:getMaxDamage()
             d.crit = item:getCriticalChance()
        end
        
        -- Check for nested items (Bag, KeyRing, etc.)
        if item.getInventory then
            local inv = item:getInventory()
            if inv and not inv:isEmpty() then
                d.items = {}
                local subItems = inv:getItems()
                for j=0, subItems:size()-1 do
                    local sub = subItems:get(j)
                    local subData = processSensorItem(sub) 
                    if subData then
                         table.insert(d.items, subData)
                    end
                end
            end
        end
        return d
    end

    -- 4. WORLD ITEMS (Items on floor)
    vision.world_items = {}
    -- Scan local area for WorldInventoryItems (Radius ~10 similar to visual range)
    -- Using a slightly smaller radius for items to avoid noise
    local ITEM_SCAN_RADIUS = 10
    local worldItems = getCell():getObjectList() -- This gets moving objects including WorldInventoryItems
    if worldItems then
        for i=0, worldItems:size()-1 do
            local obj = worldItems:get(i)
            if instanceof(obj, "IsoWorldInventoryObject") then
                local dx = obj:getX() - px
                local dy = obj:getY() - py
                local dist = math.sqrt(dx*dx + dy*dy)
                
                if dist <= ITEM_SCAN_RADIUS then
                    local item = obj:getItem()
                    if item then
                        -- Use shared helper
                        local data = processSensorItem(item)
                        
                        -- Force World Object ID (Stable)
                        data.id = tostring(obj:getID())
                        -- Inject Position
                        data.x = math.floor(obj:getX())
                        data.y = math.floor(obj:getY())
                        data.z = math.floor(obj:getZ())
                        
                        table.insert(vision.world_items, data)
                    end
                end
            end
        end
    end

    -- 5. NEARBY CONTAINERS (Lootable)
    -- Try to get exactly what the player sees via the Loot Window
    vision.nearby_containers = {}
    local lootWindow = nil
    
    -- Safety check for global getPlayerLoot function (it's part of ISUI)
    if getPlayerLoot then
        lootWindow = getPlayerLoot(playerIndex)
    end

    if lootWindow and lootWindow.inventoryPane and lootWindow.inventoryPane.inventoryPage and lootWindow.inventoryPane.inventoryPage.backpacks then
        local backpacks = lootWindow.inventoryPane.inventoryPage.backpacks
        for i, containerObj in ipairs(backpacks) do
            local inventory = nil
            -- Detect how to get inventory based on object type
            if containerObj.inventory then
                 inventory = containerObj.inventory
            elseif containerObj.getInventory then
                 inventory = containerObj:getInventory()
            elseif containerObj.getContainer then
                 local c = containerObj:getContainer()
                 if c then inventory = c end
            end
            
            -- If still nil, maybe it's the inventory itself? (Some mods do this)
            if not inventory and instanceof(containerObj, "ItemContainer") then
                inventory = containerObj
            end
            
            if inventory then
                -- Resolving the actual World Object
                -- We use the inventory's parent as the starting point (usually the Item or Object)
                local startObj = inventory:getParent() 

                -- Fix for Items acting as Containers (Bags, KeyRings)
                if not startObj and inventory.getContainingItem then
                    startObj = inventory:getContainingItem()
                end

                local invType = "Unknown"
                if inventory.getType then invType = inventory:getType() end
                
                -- Explicit Floor Check
                if invType == "floor" then
                     -- Floor "parent" is nil, so startObj remains nil.
                     -- We handle this specifically below.
                end 
                local xVal, yVal, zVal = -1, -1, -1
                local parentType = "Unknown"
                local parentId = "Unknown"
                
                -- Naming Candidate (keep track of the first Item we see)
                local nameCandidate = nil
                if invType == "floor" then
                    nameCandidate = "Floor"
                    parentType = "World"
                    parentId = "Floor" -- Fallback ID, will try to append coords later if possible?
                    -- Is the Floor always World? Yes.
                end
                
                -- Iterative Parent Walk
                local curr = startObj
                local safety = 0
                
                -- DEBUG: Trace Unknown Containers
                -- if parentType == "Unknown" (we don't know it yet) 
                local debugChain = ""
                if startObj then 
                     debugChain = tostring(startObj:getClass():getSimpleName()) 
                else
                     debugChain = "nil"
                end

                while curr and safety < 10 do
                    safety = safety + 1
                    
                    if instanceof(curr, "InventoryItem") then
                        if not nameCandidate then nameCandidate = curr:getDisplayName() end
                        
                        -- Check if on ground
                        local wi = curr:getWorldItem()
                        if wi then
                            curr = wi -- Jump to World Item
                        else
                            -- Check Container
                            local outer = curr:getContainer() -- The container holding this item
                            if outer then
                                curr = outer:getParent() -- The object holding that container
                            else
                                -- Equipped/Attached directly?
                                -- Try getOutermostContainer fallback if getContainer is nil
                                local root = curr:getOutermostContainer()
                                if root then
                                     curr = root:getParent()
                                else
                                     -- Dead end or directly on player (handled below?)
                                     break
                                end
                            end
                        end
                    elseif instanceof(curr, "IsoGameCharacter") then -- Player, Zombie, Animal
                        parentType = "Entity"
                        -- Assign ID
                        if instanceof(curr, "IsoPlayer") then parentId = "Player" .. curr:getPlayerNum()
                        elseif instanceof(curr, "IsoZombie") then parentId = "Zombie" .. curr:getID() end
                        
                        xVal, yVal, zVal = math.floor(curr:getX()), math.floor(curr:getY()), math.floor(curr:getZ())
                        break
                    elseif instanceof(curr, "IsoWorldInventoryObject") then
                        parentType = "World"
                        if curr.getID then
                             parentId = tostring(curr:getID())
                        else
                             parentId = tostring(curr:getX()) .. "_" .. tostring(curr:getY())
                        end
                        xVal, yVal, zVal = math.floor(curr:getX()), math.floor(curr:getY()), math.floor(curr:getZ())
                        
                        -- Grab name if we missed it
                        if not nameCandidate and curr.getItem then
                            local item = curr:getItem()
                            if item then nameCandidate = item:getDisplayName() end
                        end
                        break
                     elseif instanceof(curr, "IsoObject") then
                        parentType = "Object"
                        xVal, yVal, zVal = math.floor(curr:getX()), math.floor(curr:getY()), math.floor(curr:getZ())
                        parentId = xVal .. "_" .. yVal .. "_" .. zVal
                        break
                    elseif instanceof(curr, "IsoGridSquare") then
                        -- Found the Floor!
                        parentType = "World"
                        nameCandidate = "Floor"
                        parentId = curr:getX() .. "_" .. curr:getY() .. "_" .. curr:getZ()
                        xVal, yVal, zVal = curr:getX(), curr:getY(), curr:getZ()
                        break
                    else
                        -- Unknown object type in chain
                        debugChain = debugChain .. " -> " .. tostring(curr:getClass():getSimpleName())
                        -- Advance (Generic)
                        if curr.getParent then curr = curr:getParent() else break end
                    end
                end

                 -- Attempt 3: ISButton / UI Element Fallback
                if xVal == -1 and containerObj.getX and not instanceof(containerObj, "ISButton") then 
                    -- Only trust containerObj if it's not a UI element (buttons have screen X/Y, not world)
                     xVal = math.floor(containerObj:getX())
                end
                
                -- Final Fallback: Player Position
                if xVal == -1 or yVal == -1 then
                     xVal, yVal, zVal = px, py, pz
                     -- If we fell back to player pos and didn't find a parent, it's likely on the player
                     if parentType == "Unknown" then parentType = "Entity" end 
                end

                local cData = {
                    type = "Container",
                    object_type = nameCandidate or "Unknown", -- Default to Item Name if found
                    x = xVal,
                    y = yVal,
                    z = zVal,
                    items = {},
                    meta = {
                        parent_type = parentType,
                        parent_id = parentId
                    }
                }

                if cData.object_type == "Unknown" then
                     -- print("[SENSOR] Unknown Container Dump:")
                     -- print("  NameCand: " .. tostring(nameCandidate))
                     -- print("  ParentType: " .. tostring(parentType))
                     -- print("  ParentID: " .. tostring(parentId))
                     -- print("  InventoryType: " .. tostring(invType))
                     -- if containerObj and containerObj.getClass then print("  ContainerObj Class: " .. tostring(containerObj:getClass():getSimpleName())) end
                     -- if inventory and inventory.getClass then print("  Inventory Class: " .. tostring(inventory:getClass():getSimpleName())) end
                     -- if startObj and startObj.getClass then print("  StartObj (Parent) Class: " .. tostring(startObj:getClass():getSimpleName())) end
                     -- print("  Chain: " .. debugChain)
                end
                
                -- Determine type name (Fallback if not item)
                if cData.object_type == "Unknown" then
                     local function getContainerName(obj)
                        -- Try to get real name if possible (some objects have localization)
                        if obj.getContainer and obj:getContainer() and obj:getContainer():getType() then
                            -- return obj:getContainer():getType() -- often just "crate" or "bin"
                        end
                        
                        local spriteName = nil
                        if obj.getSprite and obj:getSprite() and obj:getSprite():getName() then
                            spriteName = obj:getSprite():getName()
                        end
                        
                        if spriteName then
                             -- Simple cleanup for standard sprites
                             local clean = spriteName
                             clean = string.gsub(clean, "%d", "")     -- Remove numbers
                             clean = string.gsub(clean, "_", " ")     -- Replace underscores
                             clean = string.gsub(clean, "^%s*(.-)%s*$", "%1") -- Trim
                             
                             -- Mappings for common prefixes
                             if string.find(spriteName, "appliances_refrigeration") then return "Fridge" end
                             if string.find(spriteName, "appliances_cooking") then return "Oven" end
                             if string.find(spriteName, "furniture_storage") then return "Shelf" end
                             if string.find(spriteName, "furniture_shelving") then return "Bookshelf" end
                             if string.find(spriteName, "furniture_tables") then return "Table" end
                             if string.find(spriteName, "counters") then return "Counter" end
                             
                             return clean
                        end
                        
                        if obj.getObjectName and obj:getObjectName() then
                            return obj:getObjectName()
                        end
    
                        return "Container"
                    end
                    
                    if startObj then
                         cData.object_type = getContainerName(startObj)
                         if cData.object_type == "Container" and instanceof(startObj, "IsoZombie") then cData.object_type = "ZombieCorpse" end
                         if cData.object_type == "Container" and instanceof(startObj, "IsoDeadBody") then cData.object_type = "Corpse" end
                    end
                end
                


                -- Get Items (Recursive)
                local items = inventory:getItems()
                for j=0, items:size()-1 do
                    local it = items:get(j)
                    local data = processSensorItem(it)
                    if data then table.insert(cData.items, data) end
                end
                
                table.insert(vision.nearby_containers, cData)
            end
        end
    else
        -- Fallback: Scan explicit 3x3 for containers
        local range = 1
        for x = px-range, px+range do
            for y = py-range, py+range do
                local sq = getSquare(x, y, pz)
                if sq then
                    local objs = sq:getObjects()
                    for k=0, objs:size()-1 do
                        local o = objs:get(k)
                        if o:getContainer() then
                             -- Add to list... (Simplified for brevity, assuming UI works mostly)
                        end
                    end
                end
            end
        end
    end

    -- 6. VEHICLES
    vision.vehicles = {}
    local vehicles = getCell():getVehicles()
    
    if vehicles then
        -- print("[DEBUG] Vehicles List Size: " .. tostring(vehicles:size()))
        for i=0, vehicles:size()-1 do
            local veh = vehicles:get(i)
            if veh then
                local dx = veh:getX() - px
                local dy = veh:getY() - py
                local dist = math.sqrt(dx*dx + dy*dy)
                -- Force include for debug
                if true then -- dist <= 40.0 then
                    -- Minimal Safe Scan
                    local vData = {
                        id = "vehicle_" .. veh:getId(),
                        type = "Vehicle",
                        object_type = veh:getScriptName(),
                        x = veh:getX(),
                        y = veh:getY(),
                        z = veh:getZ(),
                        meta = {
                            -- locked = veh:isLocked(),   -- CRASHING
                            -- hotwired = veh:isHotwired(),
                            -- running = veh:isEngineRunning(),
                            name = veh:getScript() and veh:getScript():getName(),
                        }
                    }

                    -- Scan Parts for Containers
                    vData.parts = {}
                    if veh.getPartCount then
                        for j=0, veh:getPartCount()-1 do
                            local part = veh:getPartByIndex(j)
                            if part and part:getItemContainer() then
                                local container = part:getItemContainer()
                                local partData = {
                                    id = part:getId(), -- e.g. "GloveBox"
                                    type = "Container",
                                    capacity = container:getCapacity(),
                                    items = {}
                                }
                                
                                -- Get Items
                                local items = container:getItems()
                                for k=0, items:size()-1 do
                                    local it = items:get(k)
                                    table.insert(partData.items, {
                                        type = it:getFullType(),
                                        name = it:getName(),
                                        count = 1
                                    })
                                end
                                
                                table.insert(vData.parts, partData)
                            end
                        end
                    end
                    
                    table.insert(vision.vehicles, vData)
                end
            end
        end
    end

    return vision
end

print(TAG .. "Loaded.")
return Sensor
