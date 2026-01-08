Handler_DirectMove = {}

function Handler_DirectMove.execute(player, args)
    if not args then
        print("[Handler_DirectMove] Error: Missing args.")
        return false
    end

    local x = args.x or 0
    local y = args.y or 0
    
    if DirectControl then
        DirectControl.setVector(x, y)
    else
        print("[Handler_DirectMove] Error: DirectControl global is nil!")
    end
    
    -- Direct Control actions are instant and don't block.
    return true 
end

return Handler_DirectMove
