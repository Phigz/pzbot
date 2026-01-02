-- Handler_Consume.lua
-- Handles "Consume" commands (Eat/Drink)

local Handler_Consume = {}
local TAG = "[Action-Consume] "

local function findItemById(player, idString)
    if not idString or not player then return nil end
    local inv = player:getInventory()
    if not inv then return nil end
    
    local items = inv:getItems()
    for i=0, items:size()-1 do
        local item = items:get(i)
        if tostring(item:getID()) == idString then
            return item
        end
    end
    return nil
end

function Handler_Consume.execute(player, params)
    local itemId = params.itemId
    if not itemId then
        print(TAG .. "Error: Missing itemId")
        return false 
    end

    local item = findItemById(player, itemId)
    if not item then
        print(TAG .. "Item not found in inventory: " .. tostring(itemId))
        return false
    end

    -- Check if edible
    if not item:getCategory() == "Food" and not item:IsFood() then
         print(TAG .. "Item is not food: " .. item:getName())
         -- Could be pills/water?
         -- Assume if user sent Consume, they want to try.
    end

    print(TAG .. "Consuming: " .. item:getName())
    
    -- Queue ISEatFood
    -- (character, foodItem, percentage=1.0)
    ISTimedActionQueue.add(ISEatFood:new(player, item, 1.0))
    
    return true
end

return Handler_Consume
