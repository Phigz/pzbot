local Handler_Sit = {}

function Handler_Sit.execute(player, params)
    print("[AISurvivorBridge] [BotCommand] Executing Sit (Brute Force Anim)")

    -- 1. Probe Player Object
    print("[AISurvivorBridge] Probing 'player' for Sit methods...")
    -- metatable is usually where methods live for Java-backed objects
    local meta = getmetatable(player)
    if meta then
        for k, v in pairs(meta) do
            if type(k) == "string" and string.find(k, "Sit") then
                print("[AISurvivorBridge] Player Method Found: " .. k)
            end
        end
    end

    -- 2. Probe ContextMenu for 'Rest'
    if ISWorldObjectContextMenu then
        for k,v in pairs(ISWorldObjectContextMenu) do
             if type(k) == "string" and string.find(k, "Rest") then
                 print("[AISurvivorBridge] ContextMenu Rest Func: " .. k)
             end
        end
    end

    -- 3. Try to force animation via variables and events
    print("[AISurvivorBridge] Setting SitAnim variable and event...")
    player:setVariable("SitAnim", "SitOnGround")
    player:reportEvent("EventSitOnGround")
    
    -- 4. Set state
    player:setSitOnGround(true)
    
    return true
end

return Handler_Sit
