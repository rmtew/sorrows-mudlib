from mudlib import Body

class Body(Body):
    def Look(self):
        return "ROOM DESCRIPTION"

    def GetLocality(self):
        return "LOCALITY"

    def MoveDirection(self, verb):
        self.user.Tell("ATTEMPTED MOVE: %s" % verb)
