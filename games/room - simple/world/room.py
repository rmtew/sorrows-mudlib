import weakref

from mudlib import util
from game.world import Container

class Room(Container):
    def __init__(self):
        Container.__init__(self)
    
        self.exits = weakref.WeakValueDictionary()

    def AddExit(self, direction, room):
        direction = util.ResolveDirection(direction)
        self.exits[direction] = room

    def GetExits(self):
        return self.exits.keys()

    def GetExitRoom(self, direction):
        return self.exits.get(direction, None)
