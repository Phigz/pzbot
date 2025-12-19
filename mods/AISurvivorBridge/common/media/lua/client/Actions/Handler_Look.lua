-- Handler_Look.lua

local Handler_Look = {}

local ISLookAction = ISBaseTimedAction:derive("ISLookAction")

function ISLookAction:isValid() return true end
function ISLookAction:update() end
function ISLookAction:start()
    if self.x and self.y then
        self.character:faceLocation(self.x, self.y)
    end
end
function ISLookAction:stop() ISBaseTimedAction.stop(self) end
function ISLookAction:perform() ISBaseTimedAction.perform(self) end
function ISLookAction:new(character, x, y)
    local o = {}
    setmetatable(o, self)
    self.__index = self
    o.character = character
    o.x = x
    o.y = y
    o.stopOnWalk = true
    o.stopOnRun = true
    o.maxTime = 20
    return o
end

function Handler_Look.execute(player, params)
    if params.target then
         local x, y = params.target.x, params.target.y
         print("[AISurvivorBridge] [BotCommand] Queuing Look At: " .. x .. "," .. y)
         ISTimedActionQueue.add(ISLookAction:new(player, x, y))
         return true
    end
    print("[AISurvivorBridge] Look requires 'target' param")
    return false
end

return Handler_Look
