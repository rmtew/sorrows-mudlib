"""
Working notes:

** We have object.MoveTo(container) as an object movement API.

  Need to consider making a world object container subclass.  Have the
  world service use that as a storage location for bodies and objects.

Outstanding problems:

** Code reloading

  * Slots.
  * Leaked temporary class references.

"""


# Encapsulate a world.

import os, random, time, collections, copy, weakref
import stackless
from stacklesslib.main import sleep as tasklet_sleep

from mudlib import Service
from game.world import Body, Object
from game.shells import RoguelikeShell

COLOUR_BLACK   = 0
COLOUR_RED     = 1
COLOUR_GREEN   = 2
COLOUR_YELLOW  = 3
COLOUR_BLUE    = 4
COLOUR_MAGENTA = 5
COLOUR_CYAN    = 6
COLOUR_WHITE   = 7

FLAG_PASSABLE = (1 << 0)
FLAG_OPAQUE   = (1 << 1)
FLAG_MARKER   = (1 << 2)

class Tile(object):
    # __slots__ = [ "character", "fgColour", "bgColour", "flags" ]
    # Causes reloading problems.
    # 1. Run game.
    # 2. Update this file.
    # 3. Existing instances of this class bomb when used.

    def __init__(self, character=" ", fgColour=None, bgColour=None, isPassable=True, isOpaque=False, isMarker=False):
        self.character = character
        self.fgColour = fgColour
        self.bgColour = bgColour
        self.flags = 0
        if isPassable:
            self.flags |= FLAG_PASSABLE
        if isOpaque:
            self.flags |= FLAG_OPAQUE
        if isMarker:
            self.flags |= FLAG_MARKER

    @property
    def isPassable(self):
        return self.flags & FLAG_PASSABLE

    @property
    def isOpaque(self):
        return self.flags & FLAG_OPAQUE

    @property
    def isMarker(self):
        return self.flags & FLAG_MARKER


START_TILE = Tile("x", isMarker=True)
SPAWN_TILE = Tile("s", isMarker=True)
WALL_TILE  = Tile("X", isPassable=False, isOpaque=True)
WALL1_TILE = Tile("1", isPassable=False, isOpaque=True)
WALL2_TILE = Tile("2", isPassable=False, isOpaque=True)
DOOR_TILE  = Tile("D", isPassable=False, isOpaque=True)
FLOOR_TILE = Tile(" ")

mapTilesByCharacter = {}
def IndexTiles():
    for k, v in globals().iteritems():
        if k.endswith("_TILE"):
            mapTilesByCharacter[v.character] = v
IndexTiles()

CHAR_TILE_TEMPLATE = Tile("@", isPassable=False)
DRAGON_TILE = Tile("&", isPassable=False)
CUBE_TILE = Tile("C", isPassable=False)

levelMap = """
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX212XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXsXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXX                      D XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXX X XXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXDXDXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXX D    XXXXXXXXXX             XXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXX    X                      XXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXX D    X XXXXXXXX             XXXXXXXXXXXXXXXX XXXXX     X     XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXX    D XXXXXXXX             XXXXXXXXXXXXXXXX XXXXX     X     XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
X     D    X XXXXXXXX             XXXXXXXXXXXXXXXX XXXXX     X     XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXX    X                      XXXXXXXXXXXXXX     XXXXXDXXXXXDXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXX D    XXXXXXXXXX             XXXXXXXX           D              D XXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXDXDXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXX     XXXXXDXXXXXDXXXX XXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXX X XXXXXXXXXXXXXXXXXXXXXXXXXXXXX     XXXXX XXXXX     X     X  X   XXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  x  XXXXX XXXXX     X     X XX   XXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     XXXXX XXXXX     X     X X    XXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXX XXXXDXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXX                           X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
"""



class WorldService(Service):
    __sorrows__ = 'world'

    # ==================================================
    # Service

    def Run(self):
        self.bodiesByUsername = {}
        self.bodies = []

        # Process the map.
        self.mapRows = [
            line.strip()
            for line in levelMap.split("\n")
            if len(line) and line[0] == WALL_TILE.character
        ]

        self.playerStartX, self.playerStartY = random.choice(self.FindTilePositions(START_TILE))
        self.npcStartX, self.npcStartY = random.choice(self.FindTilePositions(SPAWN_TILE))

        self.objectsByPosition = collections.defaultdict(lambda: [])

        self.mapWidth = len(self.mapRows[0])
        self.mapHeight = len(self.mapRows)

        stackless.tasklet(self.ManageFloraAndFauna)()

    # Events -----------------------------------------------------------------

    def OnUserEntersGame(self, user, body):
        body.SetShortDescription(user.name.capitalize())
        self.AddBody(body, self.GetPlayerStartPosition(), CHAR_TILE_TEMPLATE)

    def OnUserLeavesGame(self, user, body):
        self.RemoveBody(body)

    # API -----------------------------------------------------------------

    def AddUser(self, user):
        if self.bodiesByUsername.has_key(user.name):
            raise RuntimeError("User", user.name, "already present")

        RoguelikeShell().Setup(user.inputstack)

        body = Body(self, user)
        self.bodiesByUsername[user.name] = body
        user.SetBody(body)

        return body

    def RemoveUser(self, user):
        if not self.bodiesByUsername.has_key(user.name):
            raise RuntimeError("User", user.name, "not present")

        body = self.bodiesByUsername[user.name]
        sorrows.world.OnUserLeavesGame(user, body)

        del self.bodiesByUsername[user.name]
        user.SetBody(None)
        body.Release()

    def GetBody(self, user):
        return self.bodiesByUsername[user.name]

    def AddBody(self, body, position, tile, fgColour=None, bgColour=None):
        body.SetTile(tile, fgColour=fgColour, bgColour=bgColour)
        self.bodies.append(body)
        self._MoveObject(body, position, force=True)

    def RemoveBody(self, body):
        if body not in self.bodies:
            return
        self.bodies.remove(body)
        self._MoveObject(body, None)

    # ------------------------------------------------------------------------

    def FindTilePositions(self, tile):
        l = []
        for yOffset, line in enumerate(self.mapRows):
            xOffset = line.find(tile.character)
            while xOffset != -1:
                l.append((xOffset, yOffset))
                xOffset = line.find(tile.character, xOffset+1)
        return l

    def _AddObject(self, object_, position):
        object_.SetPosition(position)
        if position is None:
            return
        self.objectsByPosition[position].append(object_)

    def _RemoveObject(self, object_, position):
        if position is None:
            return
        self.objectsByPosition[position].remove(object_)

    def GetPlayerStartPosition(self):
        return self.playerStartX, self.playerStartY

    def GetNPCStartPosition(self):
        return self.npcStartX, self.npcStartY

    def MoveObject(self, object_, position):
        self.CheckBoundaries(*position)
        return self._MoveObject(object_, position)

    def _MoveObject(self, object_, newPosition, force=False):
        if newPosition is None:
            force = True
        else:
            tile = self._GetTile(newPosition)

        if force or self.IsTileUnoccupied(tile):
            oldPosition = object_.GetPosition()
            self._RemoveObject(object_, oldPosition)
            self._AddObject(object_, newPosition)
            # Inform all the bodies in the world.
            for body in self.bodies:
                body.OnObjectMoved(object_, oldPosition, newPosition)
            return True
        return False

    def GetObjectsAtPosition(self, position):
        return self.objectsByPosition.get(position, [])

    def GetTile(self, x, y):
        self.CheckBoundaries(x, y)
        return self._GetTile((x, y))

    def _GetTile(self, position):
        if position in self.objectsByPosition:
            candidates = []
            for object_ in self.objectsByPosition[position]:
                if isinstance(object_, Body):
                    tile = copy.copy(object_.tile)
                    candidates.append((1, tile))
                elif isinstance(object_, FireObject):
                    tile = copy.copy(FLOOR_TILE)
                    tile.bgColour = COLOUR_RED
                    candidates.append((2, tile))
                #else:    
                #    raise RuntimeError("Not implemented", object_)

            bgColour = None
            priority = 100
            tile = None
            for cPriority, cTile in candidates:
                if cPriority < priority:
                    tile = cTile
                    priority = cPriority
                if bgColour is None and cTile.bgColour is not None:
                    bgColour = cTile.bgColour
            if tile is not None:
                if bgColour is not None and tile.bgColour is None:
                    tile.bgColour = bgColour
                return tile

        # If no objects are visible, fall back on the background map.
        mapCharacter = self.mapRows[position[1]][position[0]]
        tile = mapTilesByCharacter[mapCharacter]
        if tile.isMarker:
            return FLOOR_TILE
        return tile

    def GetMapTile(self, position):
        mapCharacter = self.mapRows[position[1]][position[0]]
        tile = mapTilesByCharacter[mapCharacter]
        if tile.isMarker:
            return FLOOR_TILE
        return tile

    def IsLocationOpaque(self, x, y):
        tile = self.GetTile(x, y)
        return tile.isOpaque

    def IsTileUnoccupied(self, tile):
        return tile.isPassable

    def CheckBoundaries(self, x, y):
        if y < 0 or y >= self.mapHeight:
            raise RuntimeError("TILE ERROR/y", x, y)
        if x < 0 or x >= self.mapWidth:
            raise RuntimeError("TILE ERROR/x", x, y)

    relativeOffsets = [
        (-1, -1),
        ( 0, -1),
        ( 1, -1),
        (-1,  0),
        ( 1,  0),
        (-1,  1),
        ( 0,  1),
        ( 1,  1),
    ]

    def FindMovementDirections(self, position, mapOnly=False):
        matches = []
        for xi, yi in self.relativeOffsets:
            x, y = position
            x += xi
            y += yi
            if y < 0 or y >= self.mapHeight:
                continue
            if x < 0 or x >= self.mapWidth:
                continue
            if mapOnly:
                tile = self.GetMapTile((x, y))
            else:
                tile = self.GetTile(x, y)
            if self.IsTileUnoccupied(tile):
                matches.append((x, y))
        return matches

    # Flora and fauna --------------------------------------------------------

    # - NPC presence.  For now, define a spawning tile, and have that add
    #   three NPCs to the game as time passes.  These NPCs should wander around
    #   the dungeon freely.  Two second tick for movement.

    def ManageFloraAndFauna(self):
        stackless.tasklet(self.RunNPC, CUBE_TILE, COLOUR_YELLOW)()
        tasklet_sleep(10.0)
        stackless.tasklet(self.RunNPC, DRAGON_TILE, COLOUR_GREEN)()
        tasklet_sleep(10.0)
        stackless.tasklet(self.RunNPC, DRAGON_TILE, COLOUR_GREEN)()
        tasklet_sleep(10.0)
        stackless.tasklet(self.RunNPC, DRAGON_TILE, COLOUR_GREEN)()


    def RunNPC(self, tile, fgColour, bgColour=None):
        body = NPC(self, None)
        self.AddBody(body, self.GetNPCStartPosition(), tile, fgColour, bgColour)


class NPC(Body):
    def __init__(self, service, user=None):
        Body.__init__(self, service, user)

    def OnObjectMoved(self, object_, oldPosition, newPosition):
        if object_ is self:
            if oldPosition is None:
                stackless.tasklet(self.Wander)()

    def Wander(self):
        lastPosition = self.position
        while hasattr(sorrows, "world") and sorrows.world.IsRunning():
            currentPosition = self.position
            matches = sorrows.world.FindMovementDirections(self.position)
            if len(matches) > 1 and lastPosition in matches:
                matches.remove(lastPosition)
            if len(matches):
                lastPosition = currentPosition
                sorrows.world._MoveObject(self, random.choice(matches))

            tasklet_sleep(2.5 + -random.random())


class FireObject(Object):
    pass


class FireSource(Object):
    def __init__(self):
        Object.__init__(self)

        self.components = []
        self.componentsByPosition = {}

        stackless.tasklet(self.ManageFire)()

    def ManageFire(self):
        fireObject = FireObject()
        fireObject.generation = 0
        sorrows.world._MoveObject(fireObject, self.position, force=True)
        
        self.components.append(fireObject)
        self.componentsByPosition[self.position] = fireObject
        self.idx = -1

        tasklet_sleep(1.0)
        while hasattr(sorrows, "world") and sorrows.world.IsRunning() and len(self.components):
            if self.position is None:
                self.DieOut()
            else:
                self.Spread()

            tasklet_sleep(1.0 + -random.random() * 0.5)

    def Spread(self):
        lowWatermark = self.idx
        idx = lowWatermark + 1
        highWatermark = len(self.components)
        while idx < highWatermark:
            fireObject = self.components[idx]
            positions = sorrows.world.FindMovementDirections(fireObject.position, mapOnly=True)
            for position in positions[:]:
                if position in self.componentsByPosition:
                    positions.remove(position)
                    continue

            if len(positions):
                fireObject = FireObject()
                fireObject.generation = highWatermark
                position = random.choice(positions)
                sorrows.world._MoveObject(fireObject, position, force=True)

                self.components.append(fireObject)
                self.componentsByPosition[position] = fireObject
            else:
                if idx == lowWatermark + 1:
                    lowWatermark = idx

            idx += 1

        self.idx = lowWatermark

    def DieOut(self):
        generation = self.components[-1].generation
        while len(self.components) and self.components[-1].generation == generation:
            fireObject = self.components.pop()

            position = fireObject.position
            sorrows.world._MoveObject(fireObject, None, force=True)

            del self.componentsByPosition[position]        

