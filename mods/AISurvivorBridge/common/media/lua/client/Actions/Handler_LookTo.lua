-- Handler_LookTo.lua

local Handler_LookTo = {}

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

function Handler_LookTo.execute(player, params)
    local x, y
    if params.x and params.y then
        x, y = params.x, params.y
    elseif params.target then
        x, y = params.target.x, params.target.y
    else
        print("[AISurvivorBridge] LookTo requires x,y or target")
        return false
    end

    print("[AISurvivorBridge] [BotCommand] Queuing LookTo: " .. x .. "," .. y)
    ISTimedActionQueue.add(ISLookAction:new(player, x, y))
    return true
end

print("[AISurvivorBridge] LOAD SUCCESS: Handler_LookTo.lua")
return Handler_LookTo
