-- Sensor.lua
-- Handles scanning the environment around the player with FOV checks.
-- Optimized to use global lists for dynamic entities.

local Sensor = {}
local TAG = "[AISurvivorBridge-Sensor] "

print(TAG .. "Loading...")

-- HELPER: Process Item (Global within module)
local function processSensorItem(item)
    if not item then return nil end
    local id = tostring(item:getID())
    
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
                -- Avoid infinite recursion if item contains itself (unlikely but possible)
                if sub ~= item then
                     local subData = processSensorItem(sub) 
                     if subData then
                          table.insert(d.items, subData)
                     end
                end
            end
        end
    end
    return d
end

local function getSquare(x, y, z)
    local cell = getCell()
    if not cell then return nil end
    return cell:getGridSquare(x, y, z)
end

-- Helper: Extract Interactible Objects (Ovens/TVs/Gens) from a square
local function getInteractibleData(sq)
    local data = {}
    local objects = sq:getObjects()
    if not objects then return data end
    
    for i=0, objects:size()-1 do
        local obj = objects:get(i)
        local info = nil
        
        -- STOVE / MICROWAVE
        if instanceof(obj, "IsoStove") then
            info = {
                type = "Stove",
                activated = obj:Activated(), -- Capitalized in Java (sometimes isActivated)
                temp = obj:getCurrentTemperature()
            }
            -- Microwave check
            if obj:getContainer() and obj:getContainer():getType() == "microwave" then
                info.type = "Microwave"
            end
            
        -- GENERATOR
        elseif instanceof(obj, "IsoGenerator") then
            info = {
                type = "Generator",
                activated = obj:isActivated(),
                fuel = obj:getFuelLevel(),
                cond = obj:getCondition()
            }
            
        -- TV / RADIO (World Object)
        elseif instanceof(obj, "IsoTelevision") or instanceof(obj, "IsoRadio") then
             -- Note: IsoTelevision usually extends IsoWaveSignal
             info = { type = "TV" }
             if instanceof(obj, "IsoRadio") then info.type = "Radio" end
             
             local d = obj:getDeviceData()
             if d then
                 info.activated = d:getIsTurnedOn()
                 info.channel = d:getChannel()
                 info.vol = d:getDeviceVolume()
             end

        -- LIGHT SWITCH (Wall Switches / Lamps)
        elseif instanceof(obj, "IsoLightSwitch") then
             info = {
                 type = "Light",
                 activated = obj:isActivated(),
                 room = (sq:getRoom() and sq:getRoom():getName()) or "Unknown"
             }

        -- LAUNDRY
        elseif instanceof(obj, "IsoClothingWasher") then
             info = { type = "Washer", activated = obj:isActivated() }
        elseif instanceof(obj, "IsoClothingDryer") then
             info = { type = "Dryer", activated = obj:isActivated() }
        end

        if info then
            -- Common fields
            info.x = math.floor(obj:getX())
            info.y = math.floor(obj:getY())
            info.z = math.floor(obj:getZ())
            -- Add ID using coordinates if no real ID
            info.id = "int_" .. tostring(info.x) .. "_" .. tostring(info.y) .. "_" .. tostring(i)
            
            table.insert(data, {
                type = info.type,
                id = info.id,
                x = info.x, y = info.y, z = info.z,
                meta = info
            })
        end
    end
    return data
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

local function classifySprite(sName)
    if not sName then return nil end
    
    -- 1. Trees
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

local function scanSquare(vision, x, y, z, px, py, playerIndex)
    local sq = getSquare(x, y, z)
    local distSq = (x-px)*(x-px) + (y-py)*(y-py)
    local isClose = distSq < (8*8)
    
    if sq and (sq:isSeen(playerIndex) or isClose) then
        local isWalkable = sq:isFree(false)
        local tileData = { x = x, y = y, z = z, w = isWalkable }
             
        -- INTERACTIBLES SCAN
        local inters = getInteractibleData(sq)
        for _, inter in ipairs(inters) do
             table.insert(vision.objects, inter)
        end
        
        local room = sq:getRoom()
        if room then
            tileData.room = room:getName()
        end

        local layer = nil
         -- 1. Check Objects (Trees, Fences, etc.)
         local objs = sq:getObjects()
         if objs then
            for i=0, objs:size()-1 do
                local o = objs:get(i)
                if instanceof(o, "IsoTree") then 
                    layer = "Tree"
                    break 
                end
                local sprite = o:getSprite()
                if sprite and sprite:getName() then
                    local found = classifySprite(tostring(sprite:getName()))
                    if found then
                        layer = found
                        if layer == "Tree" or layer == "Wall" or layer == "FenceHigh" then break end
                    end
                end
            end
         end
         
         -- 2. Check Floor
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

        -- Static Object Info (Windows, Doors, Containers)
        if sq then
            local rawObjs = sq:getObjects()
            if rawObjs then
                for i=0, rawObjs:size()-1 do
                    local obj = rawObjs:get(i)
                    local objType = nil
                    local meta = {}

                    if instanceof(obj, "IsoWindow") then
                        objType = "Window"
                        meta.open = obj:getSprite() and obj:getSprite():getName() and string.find(tostring(obj:getSprite():getName()), "open")
                        if obj.isLocked then meta.locked = obj:isLocked() end
                        if obj.isPermaLocked then meta.perma = obj:isPermaLocked() end 
                    elseif instanceof(obj, "IsoDoor") then
                        objType = "Door"
                        meta.open = obj:IsOpen()
                        if obj.isLocked then meta.locked = obj:isLocked() end
                        if obj.isLockedByKey then meta.keyLocked = obj:isLockedByKey() end
                        if obj.getKeyId and obj:getKeyId() ~= -1 then meta.hasKeyId = true end
                    elseif instanceof(obj, "IsoContainer") then
                        if not instanceof(obj, "IsoMovingObject") then
                            local c = obj:getContainer()
                            local contData = {
                                id = x .. "_" .. y .. "_" .. i,
                                object_type = c:getType(),
                                x = x, y = y, z = z,
                                items = {}
                            }
                            
                            if not c:isEmpty() then
                                local items = c:getItems()
                                for j=0, items:size()-1 do
                                    local item = items:get(j)
                                    local ok, iData = pcall(processSensorItem, item)
                                    if ok and iData then
                                        table.insert(contData.items, iData)
                                    end
                                end
                            end
                            table.insert(vision.nearby_containers, contData)
                            objType = nil 
                        end
                    end
                    
                    -- SIGNAL/DEVICE
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
                                 x = x, y = y, z = z,
                                 type = sType,
                                 name = dName,
                                 on = isPower,
                                 channel = chan,
                                 volume = vol,
                                 msg = deviceMsg
                             })
                         end
                    end

                    -- CONTAINER FALLBACK
                    if not objType and obj:getContainer() and not instanceof(obj, "IsoMovingObject") then
                         local c = obj:getContainer()
                         local contData = {
                             id = x .. "_" .. y .. "_" .. i,
                             object_type = c:getType(),
                             x = x, y = y, z = z,
                             items = {}
                         }
                         if not c:isEmpty() then
                             local items = c:getItems()
                             for j=0, items:size()-1 do
                                 local item = items:get(j)
                                 local ok, iData = pcall(processSensorItem, item)
                                 if ok and iData then
                                     table.insert(contData.items, iData)
                                 end
                             end
                         end
                         table.insert(vision.nearby_containers, contData)
                         objType = nil
                    end

                    if objType then
                        local oDx = x - px
                        local oDy = y - py
                        local dist = math.sqrt(oDx*oDx + oDy*oDy)
                        meta.dist = dist
                        meta.reachable = (dist <= 2.0)
                        table.insert(vision.objects, {
                            id = x .. "_" .. y .. "_" .. i,
                            type = objType,
                            x = x, y = y, z = z,
                            meta = meta
                        })
                    end
                end
            end
        end
    end
end

function Sensor.scan(player, gridRadius)
    local ZOMBIE_RADIUS = 50.0

    local vision = {
        scan_radius = gridRadius,
        timestamp = getTimestampMs(),
        tiles = {},   
        objects = {},
        neighbors = {},
        nearby_containers = {},
        vehicles = {}, 
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

    -- 2. DYNAMIC ACTOR SCAN (Global List)
    local allObjects = getCell():getObjectList()
    local zCount = 0
    vision.debug_z = { total = -1, scan_log = "" }

    if allObjects then
        vision.debug_z.total = allObjects:size()
        local log_str = ""

        for i=0, allObjects:size()-1 do
            local obj = allObjects:get(i)
            
            -- Filter: Must be Character OR Animal
            if obj and (instanceof(obj, "IsoGameCharacter") or instanceof(obj, "IsoAnimal")) then
                
                local isSelf = (obj == player)
                if not isSelf then
                    local dx = obj:getX() - player:getX()
                    local dy = obj:getY() - player:getY()
                    local dist = math.sqrt(dx*dx + dy*dy)
                    
                    if dist <= ZOMBIE_RADIUS then
                        local zSq = obj:getCurrentSquare()
                        local seen = zSq and zSq:isSeen(playerIndex)
                        local forceInclude = instanceof(obj, "IsoAnimal")
                        
                        if seen or forceInclude then
                            local info = getActorInfo(obj, player)
                            table.insert(vision.objects, info)
                            zCount = zCount + 1
                        else
                             if instanceof(obj, "IsoAnimal") then
                                 local sqStr = "nil"
                                 if zSq then sqStr = tostring(zSq:getX())..","..tostring(zSq:getY()) end
                                 print("[SENSOR-SKIP] Animal skipped. ID:"..tostring(obj:getID()).." Dist:"..tostring(dist).." Sq:"..sqStr.." Seen:"..tostring(seen))
                             end
                        end
                    end
                end
            end
        end
        vision.debug_z.scan_log = log_str
    end

    -- 3. STATIC GRID SCAN (Tiles & Static Objects)
    local startX = px - gridRadius
    local endX   = px + gridRadius
    local startY = py - gridRadius
    local endY   = py + gridRadius

    for x = startX, endX do
        for y = startY, endY do
            scanSquare(vision, x, y, pz, px, py, playerIndex)
        end
    end
    
    -- DEBUG: Container Visibility
    local contCount = vision.nearby_containers and #vision.nearby_containers or 0
    if contCount == 0 then
        -- print(TAG.."Warning: No containers found in scan radius " .. gridRadius)
    else
        -- print(TAG.."Scan Found " .. contCount .. " containers.")
    end

    -- 4. WORLD ITEMS (Items on floor)
    vision.world_items = {}
    local ITEM_SCAN_RADIUS = 10
    local worldItems = getCell():getObjectList()
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
                        local data = processSensorItem(item)
                        data.id = tostring(obj:getID())
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
    -- vision.nearby_containers = {} -- REMOVED: Do not clear grid-scanned containers!
    local lootWindow = nil
    if getPlayerLoot then
        lootWindow = getPlayerLoot(playerIndex)
    end

    if lootWindow and lootWindow.inventoryPane and lootWindow.inventoryPane.inventoryPage and lootWindow.inventoryPane.inventoryPage.backpacks then
        local backpacks = lootWindow.inventoryPane.inventoryPage.backpacks
        for i, containerObj in ipairs(backpacks) do
            local inventory = nil
            if containerObj.inventory then
                 inventory = containerObj.inventory
            elseif containerObj.getInventory then
                 inventory = containerObj:getInventory()
            elseif containerObj.getContainer then
                 local c = containerObj:getContainer()
                 if c then inventory = c end
            end
            
            if not inventory and instanceof(containerObj, "ItemContainer") then
                inventory = containerObj
            end
            
            if inventory then
                local startObj = inventory:getParent() 

                if not startObj and inventory.getContainingItem then
                    startObj = inventory:getContainingItem()
                end

                local invType = "Unknown"
                if inventory.getType then invType = inventory:getType() end
                
                local xVal, yVal, zVal = -1, -1, -1
                local parentType = "Unknown"
                local parentId = "Unknown"
                
                local nameCandidate = nil
                if invType == "floor" then
                    nameCandidate = "Floor"
                    parentType = "World"
                    parentId = "Floor"
                end
                
                local curr = startObj
                local safety = 0
                local debugChain = ""
                if startObj then 
                     debugChain = tostring(startObj:getClass():getSimpleName()) 
                end

                while curr and safety < 10 do
                    safety = safety + 1
                    
                    if instanceof(curr, "InventoryItem") then
                        if not nameCandidate then nameCandidate = curr:getDisplayName() end
                        local wi = curr:getWorldItem()
                        if wi then
                            curr = wi 
                        else
                            local outer = curr:getContainer()
                            if outer then
                                curr = outer:getParent()
                            else
                                local root = curr:getOutermostContainer()
                                if root then
                                     curr = root:getParent()
                                else
                                     break
                                end
                            end
                        end
                    elseif instanceof(curr, "IsoGameCharacter") then 
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
                        parentType = "World"
                        nameCandidate = "Floor"
                        parentId = curr:getX() .. "_" .. curr:getY() .. "_" .. curr:getZ()
                        xVal, yVal, zVal = curr:getX(), curr:getY(), curr:getZ()
                        break
                    else
                        debugChain = debugChain .. " -> " .. tostring(curr:getClass():getSimpleName())
                        if curr.getParent then curr = curr:getParent() else break end
                    end
                end

                if xVal == -1 and containerObj.getX and not instanceof(containerObj, "ISButton") then 
                     xVal = math.floor(containerObj:getX())
                end
                
                if xVal == -1 or yVal == -1 then
                     xVal, yVal, zVal = px, py, pz
                     if parentType == "Unknown" then parentType = "Entity" end 
                end

                local cData = {
                    type = "Container",
                    object_type = nameCandidate or "Unknown",
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
                     local function getContainerName(obj)
                        if obj.getContainer and obj:getContainer() and obj:getContainer():getType() then
                            -- return obj:getContainer():getType()
                        end
                        
                        local spriteName = nil
                        if obj.getSprite and obj:getSprite() and obj:getSprite():getName() then
                            spriteName = obj:getSprite():getName()
                        end
                        
                        if spriteName then
                             local clean = spriteName
                             clean = string.gsub(clean, "%d", "") 
                             clean = string.gsub(clean, "_", " ") 
                             clean = string.gsub(clean, "^%s*(.-)%s*$", "%1")
                             
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
        local range = 1
        for x = px-range, px+range do
            for y = py-range, py+range do
                local sq = getSquare(x, y, pz)
                if sq then
                    local objs = sq:getObjects()
                    for k=0, objs:size()-1 do
                        local o = objs:get(k)
                        if o:getContainer() then
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
        for i=0, vehicles:size()-1 do
            local veh = vehicles:get(i)
            if veh then
                local dx = veh:getX() - px
                local dy = veh:getY() - py
                local dist = math.sqrt(dx*dx + dy*dy)
                -- Force include for debug
                if true then 
                    local vData = {
                        id = "vehicle_" .. veh:getId(),
                        type = "Vehicle",
                        object_type = veh:getScriptName(),
                        x = veh:getX(),
                        y = veh:getY(),
                        z = veh:getZ(),
                        meta = {
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
                                    id = part:getId(),
                                    type = "Container",
                                    capacity = container:getCapacity(),
                                    items = {}
                                }
                                
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
