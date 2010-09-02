from game.world import Container


class Body(Container):
    def __init__(self, service, user):
        Container.__init__(self)

        self.service = service
        self.user = user

    def OnObjectMoved(self, object_, oldPosition, newPosition):
        if self.user:
            self.user.shell.OnObjectMoved(object_, oldPosition, newPosition)

    if False:
        Container.__init__(self, service, user)

        self.SetPosition((0,0))
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
        extra = ""
        foundSelf = False
        if self.service.objectsByPosition.has_key(self.position):
            for object in self.service.objectsByPosition[self.position]:
                if object is self:
                    foundSelf = True
                else:
                    extra += "\r\nYou see: "+ str(object)
        return "Formless void."+ extra

    # ------------------------------------------------------------------------
    # GetLocality
    # ------------------------------------------------------------------------
    def GetLocality(self):
        return str(self.position)

    if False:
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
