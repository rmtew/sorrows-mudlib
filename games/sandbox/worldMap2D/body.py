import mudlib
from mudlib.util import AnsiText

class Body(mudlib.Body):
    def __init__(self, service, user):
        mudlib.Body.__init__(self, service, user)
        self.position = self.service.GetStartingPosition()
        # Compile all the compass directions.
        self.directionOffsets = {
            "n": ( 0, -1),
            "s": ( 0,  1),
            "e": ( 1,  0),
            "w": (-1,  0),
        }
        for dl in [ "ne", "nw", "se", "sw" ]:
            p, s = dl
            x = self.directionOffsets[p][0] + self.directionOffsets[s][0]
            y = self.directionOffsets[p][1] + self.directionOffsets[s][1]
            self.directionOffsets[dl] = (x, y)

    # ------------------------------------------------------------------------
    # Look - Interpret the world position for the viewer
    # ------------------------------------------------------------------------
    def LookString(self):
        try:
            tile = self.service.GetTile(self.position)
        except IndexError:
            return None
        if tile.isTile:
            return tile.value
        raise RuntimeError("Bad tile type", tile.value)

    # ------------------------------------------------------------------------
    # GetLocality
    # ------------------------------------------------------------------------
    def GetLocality(self):
        width = 2
        height = 2
        s1 = "\x1b[7m       \x1b[27m\r\n"
        for y in range(-width, width+1):
            s2 = "\x1b[7m \x1b[27m"
            for x in range(-height, height+1):
                try:
                    key = self.service.GetTile(self.position, (x, y)).key
                    if key == "#":
                        token = ","
                        colour = "Green"
                    elif key == "g":
                        token = " "
                        colour = "Green"
                    elif key == "r":
                        token = " "
                        colour = "Blue"
                    else:
                        colour = None
                    if colour is not None:
                        key = AnsiText(token, colour=colour)
                    s2 += key
                except:
                    s2 += " "
            s1 += s2 +"\x1b[7m \x1b[27m\r\n"
        return s1 +"\x1b[7m       \x1b[27m"

    # ------------------------------------------------------------------------
    # MoveDirection - Handle movement of this object in a direction
    # ------------------------------------------------------------------------
    def MoveDirection(self, direction):
        offsets = self.directionOffsets[direction]
        try:
            self.service.MoveObject(self, offsets)
        except RuntimeError, e:
            if e.args[0] == "MovementFailure":
                self.user.Tell(e.args[1])
            else:
                raise

    # ------------------------------------------------------------------------
    # SetPosition
    # ------------------------------------------------------------------------
    def SetPosition(self, position):
        self.position = position
