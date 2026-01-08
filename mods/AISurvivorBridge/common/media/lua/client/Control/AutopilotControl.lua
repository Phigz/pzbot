-- AutopilotControl.lua
-- Manages the "Master Switch" for the bot.
-- Provides a UI element (Context Menu or persistent button) to toggle Autopilot.

local AutopilotControl = {}
_G.AISurvivorBridge_Autopilot = AutopilotControl

AutopilotControl.enabled = true -- Default to Enabled

function AutopilotControl.isEnabled()
    return AutopilotControl.enabled
end

function AutopilotControl.toggle()
    AutopilotControl.enabled = not AutopilotControl.enabled
    local status = AutopilotControl.enabled and "ENABLED" or "DISABLED"
    print("[AISurvivorBridge] Autopilot " .. status)
    
    local player = getPlayer()
    if player then
        player:Say("Autopilot: " .. status)
    end
end

-- Add Context Menu option
local function onFillWorldObjectContextMenu(player, context, worldObjects, test)
    local option = context:addOption("AISurvivor: Toggle Autopilot", nil, AutopilotControl.toggle)
    if AutopilotControl.enabled then
        option.iconTexture = getTexture("media/ui/tick.png") -- improving visual feedback if possible, or just text
    end
end

Events.OnFillWorldObjectContextMenu.Add(onFillWorldObjectContextMenu)

return AutopilotControl
