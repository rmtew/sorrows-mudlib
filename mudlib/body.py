from mudlib import Object

class Body(Object):
    def __init__(self, service, user):
        super(Body, self).__init__(service)

        self.service = service
        self.user = user

    def Release(self):
        super(Body, self).Release()

    # ------------------------------------------------------------------------
    # Methods body subclasses need to override.

    def LookString(self):
        """ Stub: Interpret the world description for the viewer.  """
        raise NotImplementedError

    def GetLocality(self):
        """ Stub: Not sure. """
        raise NotImplementedError

    def MoveDirection(self, verb):
        """ Stub: Move the player in the given direction. """
        raise NotImplementedError
