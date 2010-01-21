from mudlib import Object

class Body(Object):
    def __init__(self, service, user):
        Object.__init__(self, service)

        self.service = service
        self.user = user

    def Release(self):
        Object.Release(self)

    # ------------------------------------------------------------------------
    # Methods body subclasses need to override.

    def Look(self):
        """ Stub: Interpret the world description for the viewer.  """
        raise NotImplementedError

    def GetLocality(self):
        """ Stub: Not sure. """
        raise NotImplementedError

    def MoveDirection(self, verb):
        """ Stub: Move the player in the given direction. """
        raise NotImplementedError
