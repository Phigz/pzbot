-- Navigation/AStar.lua
local AStar = {}
local PathCost = require "Navigation/PathCost"

-- Helper for priority queue (min-heap would be faster, but simple table sort is mvp)
local function getLowestF(openList)
    local lowest = nil
    for _, node in pairs(openList) do
        if not lowest or node.f < lowest.f then
            lowest = node
        end
    end
    return lowest
end

local function distInfo(sq1, sq2)
    -- Euclidean distance
    local dx = sq1:getX() - sq2:getX()
    local dy = sq1:getY() - sq2:getY()
    return math.sqrt(dx*dx + dy*dy)
end

function AStar.findPath(sx, sy, sz, tx, ty, tz, limit)
    -- 1. Setup
    local cell = getCell()
    local startSq = cell:getGridSquare(sx, sy, sz)
    local targetSq = cell:getGridSquare(tx, ty, tz)
    
    if not startSq or not targetSq then
        print("[AStar] Start or Target square irrelevant (not loaded?)")
        return nil 
    end
    
    -- Limit recursion/loops
    local MAX_NODES = limit or 200 
    
    local openList = {}
    local closedList = {}
    
    -- Node structure: { sq=IsoGridSquare, x, y, z, p=parent, g=costFromStart, h=heuristic, f=total }
    -- Map key: "x_y_z"
    local function getKey(sq) return sq:getX().."_"..sq:getY().."_"..sq:getZ() end
    
    local startNode = {
        sq = startSq,
        x = sx, y = sy, z = sz,
        g = 0,
        h = distInfo(startSq, targetSq),
        f = 0,
        parent = nil
    }
    startNode.f = startNode.h
    
    openList[getKey(startSq)] = startNode
    
    local nodesChecked = 0
    
    local function isNotEmpty(t)
        for _,_ in pairs(t) do return true end
        return false
    end
    
    while isNotEmpty(openList) and nodesChecked < MAX_NODES do
        nodesChecked = nodesChecked + 1
        
        -- Pop lowest F
        local current = getLowestF(openList)
        if not current then break end
        
        local cKey = getKey(current.sq)
        openList[cKey] = nil
        closedList[cKey] = current
        
        -- Goal Check (Loose check: Distance < 1)
        if distInfo(current.sq, targetSq) < 1.0 then
            -- Reconstruct Path
            local path = {}
            local curr = current
            while curr do
                table.insert(path, 1, curr.sq)
                curr = curr.parent
            end
            return path
        end
        
        -- Neighbors
        local neighbors = {}
        local cx, cy, cz = current.x, current.y, current.z
        
        -- 3x3 Grid
        for dy = -1, 1 do
            for dx = -1, 1 do
                if not (dx == 0 and dy == 0) then
                    local nx, ny = cx + dx, cy + dy
                    local nSq = cell:getGridSquare(nx, ny, cz)
                    if nSq then
                        table.insert(neighbors, nSq)
                    end
                end
            end
        end
        
        for _, nSq in ipairs(neighbors) do
            local nKey = getKey(nSq)
            if not closedList[nKey] then
                
                -- Calculate Cost
                local cost = PathCost.getCost(nSq)
                
                -- Diagonal Penalty (approx 1.4)
                -- If dx != 0 and dy != 0 then cost = cost * 1.4 end
                
                if cost < PathCost.COST_BLOCKED then
                     local gScore = current.g + cost
                     
                     local existing = openList[nKey]
                     if not existing or gScore < existing.g then
                         -- Found better path or new node
                         local hScore = distInfo(nSq, targetSq)
                         local newNode = {
                             sq = nSq,
                             x = nSq:getX(), y = nSq:getY(), z = nSq:getZ(),
                             g = gScore,
                             h = hScore,
                             f = gScore + hScore,
                             parent = current
                         }
                         openList[nKey] = newNode
                     end
                end
            end
        end
    end
    
    print("[AStar] No path found within limit ("..nodesChecked..")")
    return nil
end

return AStar
