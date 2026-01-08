# Lua Environment Map
A living map of the Project Zomboid Lua API structure, determining what is accessible to our modding bridge.

```
Lua Environment (Global)
│
├── Globals / Singletons
│   ├── getCell() -> IsoCell
│   │   ├── getGridSquare(x, y, z) -> IsoGridSquare
│   │   └── getObjectList() -> ArrayList<IsoMovingObject>
│   │
│   ├── getPlayer() / getSpecificPlayer(0) -> IsoPlayer
│   │
│   └── AnimalPopulationManager (Target)
│       └── [MISSING / NIL] - Not exposed in current build context?
│
├── Classes (zombie.*)
│   │
│   ├── characters
│   │   ├── IsoPlayer
│   │   │   ├── getX(), getY(), getZ()
│   │   │   ├── getCurrentSquare() -> IsoGridSquare
│   │   │   └── getMoodles() -> Moodles (UserData, Opaque)
│   │   │
│   │   ├── IsoZombie
│   │   │   └── isDead()
│   │   │
│   │   └── IsoAnimal (Partially Verified)
│   │       ├── new() -> IsoAnimal (Instance created with Name:null)
│   │       ├── new(IsoCell) -> IsoAnimal
│   │       ├── [FAIL] new(IsoCell, IsoGridSquare, String) -> "No implementation found"
│   │       ├── setType(String) -> Callable
│   │       ├── setBreed(String) -> Callable
│   │       └── addToWorld() -> Callable
│   │
│   └── vehicles
│       └── BaseVehicle
│           └── [Constructor] IsoVehicle.new(IsoCell, IsoGridSquare, BaseVehicle, String type)
│
│   └── radio
│       ├── ZomboidRadio
│       │   ├── getInstance() -> ZomboidRadio
│       │   └── getDevices() -> ArrayList<DeviceData>
│       │
│       └── devices
│           ├── DeviceData
│           │   ├── getDeviceName() -> String
│           │   ├── getIsTurnedOn() -> boolean
│           │   ├── getChannel() -> int
│           │   ├── getDeviceVolume() -> float
│           │   ├── hasMedia() -> boolean
│           │   └── getMediaData() -> MediaData
│           └── MediaData
│               ├── getTitle() -> String
│               └── getCategory() -> String
│
└── Enums / Static
    └── zombie.characters.IsoGameCharacter.Breed
        └── [UNVERIFIED] - lookup failed in Lua.
```

## Observations
- **UserData Opacity**: Java objects returned to Lua (like `IsoAnimal` instances) are UserData. They do not respond to `pairs()` enumeration. Methods must be known/guessed to be called.
- **Constructor quirks**: `IsoAnimal` constructor exists but requires specific initialization to avoid "null type" errors.
