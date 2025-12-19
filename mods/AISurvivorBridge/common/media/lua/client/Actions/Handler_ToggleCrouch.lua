-- Handler_ToggleCrouch.lua

local Handler_ToggleCrouch = {}

function Handler_ToggleCrouch.execute(player, params)
    local active = params.active
    if active == nil then 
        -- toggle if not specified? Or default to true?
        -- Let's require explicit state for bots usually.
        print("[AISurvivorBridge] ToggleCrouch requires 'active' boolean")
        return false
    end

    print("[AISurvivorBridge] [BotCommand] Executing ToggleCrouch: " .. tostring(active))
    
    -- Sneak is usually instant state, not a timed action.
    -- But we can wrap it if we want to queue it.
    -- For now, immediate execution.
    player:setSneaking(active)
    
    return true
end

print("[AISurvivorBridge] LOAD SUCCESS: Handler_ToggleCrouch.lua")
return Handler_ToggleCrouch
