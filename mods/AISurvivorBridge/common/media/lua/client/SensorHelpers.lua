
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
