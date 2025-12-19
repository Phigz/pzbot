-- Handler_Wait.lua

local Handler_Wait = {}

local ISWaitAction = ISBaseTimedAction:derive("ISWaitAction")
function ISWaitAction:isValid() return true end
function ISWaitAction:update() end
function ISWaitAction:start() end
function ISWaitAction:stop() ISBaseTimedAction.stop(self) end
function ISWaitAction:perform() ISBaseTimedAction.perform(self) end
function ISWaitAction:new(character, timeMs)
    local o = {}
    setmetatable(o, self)
    self.__index = self
    o.character = character
    o.stopOnWalk = true
    o.stopOnRun = true
    o.maxTime = math.max(1, math.floor(timeMs * 0.06))
    return o
end

function Handler_Wait.execute(player, params)
    local duration = params.duration_ms or 1000
    print("[AISurvivorBridge] [BotCommand] Queuing Wait for " .. duration .. "ms")
    ISTimedActionQueue.add(ISWaitAction:new(player, duration))
    return true
end

return Handler_Wait
