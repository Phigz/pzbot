# PZBot Input Schema (`input.json`)

This document describes the structure of the JSON payload sent from the Python Runtime (`pzbot`) to the Lua Mod (`AISurvivorBridge`).

## Root Object
| Field | Type | Description |
|---|---|---|
| `actions` | `List[Action]` | Sequence of actions to perform. |

## Action Structure
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Unique UUID for the action. |
| `type` | `string` | Action type (e.g. `MoveTo`, `Wait`). |
| `params` | `dict` | Parameter key-values specific to the action type. |

## Supported Action Types

### `MoveTo`
Navigate to a target coordinate.
**Params:**
*   `x` (float): Target X.
*   `y` (float): Target Y.
*   `z` (float): Target Z (default 0).

### `Wait`
Stand still for a duration.
**Params:**
*   `duration` (int): Time to wait in milliseconds.

### `Attack`
Attack a target entity.
**Params:**
*   `targetId` (string): UUID of the target entity.

### `Loot`
Take an item from a container or world.
**Params:**
*   `targetId` (string): ID of container or item.
*   `itemId` (string): ID of the specific item inside (if container).

### `Equip`
Equip an item.
**Params:**
*   `itemId` (string): Item to equip.
*   `slot` (string): `Primary`, `Secondary`, or `Both`.

### `Interact`
Interact with an object (Door, Switch, etc).
**Params:**
*   `targetId` (string): ID of the object.
*   `action` (string): `Toggle`, `Open`, `Close`.

## Example Payload
```json
{
  "actions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "MoveTo",
      "params": {
        "x": 10840.5,
        "y": 9320.0,
        "z": 0
      }
    }
  ]
}
```
