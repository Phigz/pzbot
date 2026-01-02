-- Handler_Loot.lua
-- Executed by ActionExecutor.lua
-- Params: { itemId = "...", targetId = "..." }

local Handler_Loot = {}

function Handler_Loot.execute(player, params)
    print("[Handler_Loot] Executing Loot for Item: " .. tostring(params.itemId))

    local itemId = params.itemId
    local targetId = params.targetId -- Container ID or 'floor'

    if not itemId then
        print("[Handler_Loot] Error: No itemId provided.")
        return false
    end

    -- 1. Find the Item
    local foundItem = nil
    
    -- Check Floor (WorldItems)
    local squares = getCell():getGridSquare(player:getX(), player:getY(), player:getZ())
    -- We might need to scan nearby squares if we are slightly off?
    -- For now, check current and immediate neighbors
    local range = 2
    local z = player:getZ()
    
    for x = player:getX()-1, player:getX()+1 do
        for y = player:getY()-1, player:getY()+1 do
            local sq = getCell():getGridSquare(x, y, z)
            if sq then
                -- Check World Objects (Floor)
                local worldObjects = sq:getWorldObjects()
                for i=0, worldObjects:size()-1 do
                    local wo = worldObjects:get(i)
                    local item = wo:getItem()
                    if item then
                        -- Check by ID or Type
                        -- Note: item:getID() returns a long value, might need conversion or string match
                        -- item:getFullType() e.g. "Base.Axe"
                        if tostring(item:getID()) == tostring(itemId) or item:getFullType() == itemId then
                            print("[Handler_Loot] Found item on floor at " .. x .. "," .. y)
                            -- Grab Action
                            ISInventoryPage.renderDirty = true
                            ISTimedActionQueue.add(ISGrabItemAction:new(player, wo, 50))
                            return true
                        end
                    end
                end
                
                -- Check Containers on this square (Crates, Shelves)
                local objects = sq:getObjects()
                for i=0, objects:size()-1 do
                    local obj = objects:get(i)
                    local container = obj:getContainer()
                    if container then
                        -- Search inside
                        local items = container:getItems()
                        for j=0, items:size()-1 do
                            local item = items:get(j)
                             if tostring(item:getID()) == tostring(itemId) or item:getFullType() == itemId then
                                print("[Handler_Loot] Found item in container at " .. x .. "," .. y)
                                -- Transfer Action
                                -- ISInventoryTransferAction:new(character, item, srcContainer, destContainer, time)
                                ISTimedActionQueue.add(ISInventoryTransferAction:new(player, item, container, player:getInventory(), 20))
                                return true
                             end
                        end
                    end
                end
            end
        end
    end

    print("[Handler_Loot] Item not found in range.")
    return false
end

return Handler_Loot
