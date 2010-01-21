
from mudlib import Service
from game.world import Body

class WorldService(Service):
    __sorrows__ = 'world'

    def Run(self):
        self.bodiesByUsername = {}

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

    # ========================================================================
    # OnObjectMoved - Track movement of objects.
    # ========================================================================
    def OnObjectMoved(self, object, newPosition):
        pass

    # ========================================================================
    # OnObjectReleased - Clean up after a released object.
    # ========================================================================
    def OnObjectReleased(self, object):
        pass
