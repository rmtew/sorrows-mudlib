# Encapsulate a world.

import os, random, time, collections

from mudlib import Service
from game.world import Body
from game.shells import RoguelikeShell

START_TILE = "x"
WALL_TILE =  "X"
DOOR_TILE =  "D"
FLOOR_TILE = " "

PASSABLE_TILES = (DOOR_TILE, START_TILE, FLOOR_TILE)
OPAQUE_TILES = (WALL_TILE,)

TILE_MAP = {
    START_TILE: FLOOR_TILE,
}

levelMap = """
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
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
            if len(line) and line[0] == WALL_TILE
        ]
        for yOffset, line in enumerate(self.mapRows):
            xOffset = line.find(START_TILE)
            if xOffset != -1:
               self.playerStartX = xOffset
               self.playerStartY = yOffset
               break
        else:
            raise Exception("Map did not provide a player starting position")

        self.objectsByPosition = collections.defaultdict(lambda: [])

        self.mapWidth = len(self.mapRows[0])
        self.mapHeight = len(self.mapRows)

    def OnUserEntersGame(self, user, body):
        body.SetShortDescription(user.name.capitalize())
        self.bodies.append(body)
        self._MoveObject(body, self.GetPlayerStartPosition(), force=True)

    def OnUserLeavesGame(self, user, body):
        if body not in self.bodies:
            return
        self.bodies.remove(body)
        self._MoveObject(body, None)

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

    # ------------------------------------------------------------------------

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

    def MoveObject(self, object_, position):
        self.CheckBoundaries(*position)
        return self._MoveObject(object_, position)

    def _MoveObject(self, object_, newPosition, force=False):
        if newPosition is None:
            tile = PASSABLE_TILES[0]
        else:
            tile = self._GetTile(newPosition)

        if force or tile in PASSABLE_TILES:
            # passableTile = passableTile or tile == DOOR_TILE and (True or self.GetTileBits(newX, newY, TILE_OPEN))
            oldPosition = object_.GetPosition()

            self._RemoveObject(object_, oldPosition)
            self._AddObject(object_, newPosition)
            
            # Inform all the bodies in the world.
            for body in self.bodies:
                body.OnObjectMoved(object_, oldPosition, newPosition)

            return True
        return False

    def GetTile(self, x, y):
        self.CheckBoundaries(x, y)
        return self._GetTile((x, y))

    def _GetTile(self, position):
        # TODO: Should sort through this, seeing what is in there.
        if position in self.objectsByPosition and len(self.objectsByPosition[position]):
            return "@"
        tile = self.mapRows[position[1]][position[0]]
        return TILE_MAP.get(tile, tile)

    def IsOpaque(self, x, y):
        tile = self.GetTile(x, y)
        return tile in OPAQUE_TILES

    def CheckBoundaries(self, x, y):
        if y < 0 or y >= self.mapHeight:
            raise RuntimeError("TILE ERROR/y", x, y)
        if x < 0 or x >= self.mapWidth:
            raise RuntimeError("TILE ERROR/x", x, y)
