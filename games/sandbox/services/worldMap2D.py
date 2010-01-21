# Encapsulate a world.

import os, random

from mudlib import Service
from game.worldMap2D import Body

class WorldMap2DService(Service):
    __sorrows__ = 'worldMap2D'

    # ==================================================
    # Service

    def Run(self):
        self.bodiesByUsername = {}

        # Read and process the map file.
        mapFilename = "map.txt"
        mapPath = os.path.join(sorrows.services.gameDataPath, mapFilename)

        self.mapTilesByKey = {}

        class Tile:
            isSubmap = 0
            isTile = 0
            def __init__(self, key, value):
                self.key = key
                if value.startswith('"') and value.endswith('"'):
                    self.isTile = 1
                    value = value[1:-1]
                else:
                    self.isSubmap = 1
                self.value = value
        idx = -1
        lines = []
        for line in open(mapPath, "r"):
            if not line.startswith(" "):
                if idx == -1:
                    idx = line.find(" ")
                if idx != -1:
                    suffix = line[idx+1:].strip()
                    if len(suffix):
                        k, v = suffix.split("=")
                        self.mapTilesByKey[k] = Tile(k, v)
                lines.append(line[:idx])

        self.mapWidth = idx
        self.mapHeight = len(lines)
        self.mapRows = lines

        print "WorldMap2D: Read map \"%s\", %dx%d" % (mapFilename, self.mapWidth, self.mapHeight)

    # ==================================================
    # Support

    def GetTile(self, position, offset=None):
        if offset is not None:
            position = self.GetOffsetPosition(position, offset)
        x, y = position
        return self.mapTilesByKey[self.mapRows[y][x]]

    def GetRandomPosition(self):
        x = random.randrange(0, self.mapWidth-1)
        y = random.randrange(0, self.mapHeight-1)
        return x, y

    def GetStartingPosition(self):
        return self.GetRandomPosition()

    def GetOffsetPosition(self, position, offset):
        x = position[0] + offset[0]
        if x < 0 or x > self.mapWidth-1:
            raise RuntimeError("OutOfBounds.x", x)
        y = position[1] + offset[1]
        if y < 0 or y > self.mapHeight-1:
            raise RuntimeError("OutOfBounds.y", x)
        return x, y

    def AddUser(self, user):
        if self.bodiesByUsername.has_key(user.name):
            raise RuntimeError("User", user.name, "already present")
        body = Body(self, user)
        self.bodiesByUsername[user.name] = body
        user.SetBody(body)
        return body

    def RemoveUser(self, user):
        if not self.bodiesByUsername.has_key(user.name):
            raise RuntimeError("User", user.name, "not present")
        body = self.bodiesByUsername[user.name]
        del self.bodiesByUsername[user.name]
        user.SetBody(None)
        body.Release()

    def GetBody(self, user):
        return self.bodiesByUsername[user.name]

    def MoveObject(self, body, offset):
        try:
            position = self.GetOffsetPosition(body.position, offset)
        except:
            raise RuntimeError("MovementFailure", "There seems to be something preventing your movement in that direction.")
        tile = self.GetTile(position)
        if tile.key == "r":
            raise RuntimeError("MovementFailure", "The river is too dangerous to cross.")
        body.SetPosition(position)

    def OnObjectReleased(self, object):
        # Make sure the object is unindexed.
        pass
