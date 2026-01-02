-- Handler_Transfer.lua
-- Handles moving items between containers (Looting/Transferring)

local Handler_Transfer = {}
local TAG = "[Action-Transfer] "

if not ISInventoryTransferAction then require "TimedActions/ISInventoryTransferAction" end
if not ISWalkToTimedAction then require "TimedActions/ISWalkToTimedAction" end
-- Use standard Wait Action
if not ISWaitAction then require "TimedActions/ISWaitAction" end


local function getSquare(x, y, z)
    local cell = getCell()
    if not cell then return nil end
    return cell:getGridSquare(x, y, z)
end

local function getBestAdjacentSquare(targetSq, player)
    if not targetSq or not player then return nil end
    
    -- If target itself is walkable and not holding a solid object, we might walk there.
    -- But usually containers like crates block movement.
    -- Let's check neighbors.
    local candidates = {}
    local px, py = player:getX(), player:getY()
    
    local dirs = {
        {0, -1}, {0, 1}, {1, 0}, {-1, 0}, -- Cardinals
        {1, -1}, {-1, -1}, {1, 1}, {-1, 1} -- Diagonals
    }
    
    for _, off in ipairs(dirs) do
        local nx = targetSq:getX() + off[1]
        local ny = targetSq:getY() + off[2]
        local nSq = getSquare(nx, ny, targetSq:getZ())
        
        if nSq and nSq:isFree(false) then
            local dist = math.sqrt((nx-px)^2 + (ny-py)^2)
            table.insert(candidates, {sq=nSq, dist=dist})
        end
    end
    
    table.sort(candidates, function(a,b) return a.dist < b.dist end)
    
    return candidates[1] and candidates[1].sq or targetSq
end

function Handler_Transfer.execute(player, params)
    -- params: { itemId=..., containerId=..., destContainerId=... (optional, default: playerInv), mode="single"|"all" }
    
    local mode = params.mode or "single"
    local itemId = params.itemId
    local srcContainerId = params.containerId
    local destContainerId = params.destContainerId
    
    local playerInv = player:getInventory()
    local destContainerObj = playerInv -- Default to Looting (Player Inv)

    -- RESOLVE DESTINATION (If provided)
    if destContainerId then
        -- Similar logic to src parsing could be here, but for now assuming Looting (Player) is primary use case.
        -- TODO: Implement parsing for destContainerId if we want to "Put away" items.
        print(TAG.."Destination ID provided but not fully implemented. Defaulting to Player Inventory.")
    end

    if mode == "single" and itemId then
        print(TAG.."Transferring Item: "..tostring(itemId).." from: "..tostring(srcContainerId).." to: Inventory")
        
        local srcContainerObj = nil
        local targetSq = nil
        
        if srcContainerId then
             local x, y, i = string.match(srcContainerId, "(%d+)_(%d+)_(%d+)")
             if x and y and i then
                 targetSq = getCell():getGridSquare(tonumber(x), tonumber(y), 0)
                 
                 if targetSq then
                     -- Scan for Container
                     local objects = targetSq:getObjects()
                     local idx = tonumber(i)
                     
                     -- 1. Try Direct
                     if objects and idx < objects:size() then
                         local obj = objects:get(idx)
                         if obj then
                             if instanceof(obj, "IsoContainer") then srcContainerObj = obj:getContainer() 
                             elseif obj.getContainer then srcContainerObj = obj:getContainer() end
                         end
                     end
                     
                     -- 2. Fallback Scan
                     if not srcContainerObj then
                        print(TAG.."Direct index check failed. Scanning square for item holder...")
                        for k=0, objects:size()-1 do
                            local obj = objects:get(k)
                            local c = obj:getContainer()
                            if not c and obj.getContainer then c = obj:getContainer() end
                            
                            if c then
                                local items = c:getItems()
                                for j=0, items:size()-1 do
                                    if tostring(items:get(j):getID()) == tostring(itemId) then
                                        srcContainerObj = c
                                        print(TAG.."Found correct container at index " .. k)
                                        break
                                    end
                                end
                            end
                            if srcContainerObj then break end
                        end
                     end
                 else
                    print(TAG.."Target Square " .. x .. "," .. y .. " is not loaded.")
                 end
             end
        end
        
        if not srcContainerObj then
             print(TAG.."ERROR: Source container could not be resolved.")
             return false
        end
        
        -- 2. Find Item Logic
        local targetItem = nil
        local items = srcContainerObj:getItems()
        for j=0, items:size()-1 do
            local item = items:get(j)
            if tostring(item:getID()) == tostring(itemId) then
                 targetItem = item
                 break
            end
        end
        
        if targetItem then
             print(TAG.."Item found: "..tostring(targetItem:getName()).." ("..tostring(itemId)..")")
             
             local actionQueue = ISTimedActionQueue.getTimedActionQueue(player)
             local qSize = "unknown"
             if actionQueue and actionQueue.queue and actionQueue.queue.size then
                 qSize = tostring(actionQueue.queue:size())
             end
             print(TAG.."Current Queue Size: " .. qSize)
             
             -- QUEUE 1: Walk To
             if targetSq then
                local navTarget = getBestAdjacentSquare(targetSq, player)
                local dist = math.sqrt(math.pow(navTarget:getX() - player:getX(), 2) + math.pow(navTarget:getY() - player:getY(), 2))
                
                print(TAG.."Nav Target: "..navTarget:getX()..","..navTarget:getY().." (Dist: " .. tostring(dist) .. ")")
                
                -- Check standard distance or if we need to move
                -- If we are roughly at the neighbor, we are good.
                if dist > 0.5 then
                    print(TAG.."Queueing WalkTo: " .. tostring(navTarget:getX()) .. "," .. tostring(navTarget:getY()))
                    ISTimedActionQueue.add(ISWalkToTimedAction:new(player, navTarget))
                    
                    -- Buffer: Wait
                    if ISWaitAction then
                        print(TAG.."Queueing Wait(20)")
                        ISTimedActionQueue.add(ISWaitAction:new(player, 20)) 
                    end
                else
                    print(TAG.."Already at neighbor ("..dist.."). Skipping WalkTo.")
                end
             end
             
             -- QUEUE 2: Face Container (Robustness)
             if srcContainerObj and srcContainerObj:getParent() then
                  local parent = srcContainerObj:getParent()
                  -- Force face look logic if needed, but WalkTo should orient us mostly.
                  -- Sometimes a Face action is useful:
                  -- ISTimedActionQueue.add(ISFaceObject:new(player, parent)) (Hypothetical)
             end

             -- QUEUE 3: Transfer
             print(TAG.."Queueing TransferAction...")
             local action = ISInventoryTransferAction:new(player, targetItem, srcContainerObj, destContainerObj)
             
             -- Hook into action to debug start/finish? No easy way without wrapper.
             -- But we can print before adding.
             ISTimedActionQueue.add(action)
             
             print(TAG.."Actions Queued Successfully.")
             return true
        else
            print(TAG.."Item " .. itemId .. " NOT found in resolved container after scan.")
            return false
        end

    elseif mode == "all" and srcContainerId then
        print(TAG.."Transfer All from: "..tostring(srcContainerId))
        
        local srcContainerObj = nil
        local targetSq = nil
        
        -- 1. Resolve Container
        local x, y, i = string.match(srcContainerId, "(%d+)_(%d+)_(%d+)")
        if x and y and i then
             targetSq = getCell():getGridSquare(tonumber(x), tonumber(y), 0)
             if targetSq then
                 local objects = targetSq:getObjects()
                 local idx = tonumber(i)
                 
                 -- Try Direct
                 if objects and idx < objects:size() then
                     local obj = objects:get(idx)
                     if instanceof(obj, "IsoContainer") then srcContainerObj = obj:getContainer() 
                     elseif obj.getContainer then srcContainerObj = obj:getContainer() end
                 end
                 
                 -- Fallback Scan
                 if not srcContainerObj then
                    print(TAG.."Direct index check failed for ALL. Scanning square...")
                    -- For 'All', we don't have a specific item ID to check against.
                    -- Rely strictly on matching the container TYPE or just blindly taking the first non-empty container?
                    -- Better: Match the index as best as possible or check if *any* container exists at that index?
                    -- Actually, if index shifted, we might be screwing up.
                    -- But usually 'All' comes from a UI that just got refreshed.
                    -- Let's stick to direct index for 'All' or simple type match if known.
                    -- Current fallback for 'Single' relies on itemId.
                    -- Here we don't have it.
                    -- Let's just trust the index for now, or scan for *any* container if index fails?
                    -- Scanning for *any* container might loot the wrong thing (e.g. Fridge instead of Freezer).
                 end
             end
        end

        if not srcContainerObj then
            print(TAG.."Source container not found for Transfer All.")
            return false
        end
        
        -- QUEUE 1: Walk To
        if targetSq then
            print(TAG.."Queueing WalkTo (All): " .. tostring(targetSq:getX()) .. "," .. tostring(targetSq:getY()))
            ISTimedActionQueue.add(ISWalkToTimedAction:new(player, targetSq))
            if ISWaitAction then
                ISTimedActionQueue.add(ISWaitAction:new(player, 20)) 
            end
        end
        
        -- QUEUE 2: Transfer Loop
        local items = srcContainerObj:getItems()
        if items and not items:isEmpty() then
             print(TAG.."Transferring " .. items:size() .. " items.")
             
             -- Clone list to avoid iteration issues during removal (though ActionQueue doesn't remove immediately)
             local transferList = {}
             for j=0, items:size()-1 do
                 table.insert(transferList, items:get(j))
             end
             
             for _, item in ipairs(transferList) do
                 ISTimedActionQueue.add(ISInventoryTransferAction:new(player, item, srcContainerObj, destContainerObj))
             end
             return true
        else
            print(TAG.."Container is empty.")
            return false
        end

    end

    return false
end

return Handler_Transfer
