
from mudlib import Service
from game.world import Body, Room, Object, Container

class WorldService(Service):
    __sorrows__ = 'world'

    def Run(self):
        self.bodiesByUsername = {}
        
        ## World content.
        
        room = self.startingRoom = Room()
        room.SetShortDescription("A room")
        room.SetLongDescription("This is a room.")

        ob = Object()
        ob.SetShortDescription("brown pants")
        ob.SetLongDescription("This is a pair of brown pants.")
        ob.MoveTo(room)

        ob = Object()
        ob.SetShortDescription("green pants")
        ob.SetLongDescription("This is a pair of green pants.")
        ob.MoveTo(room)

        ob = Container()
        ob.SetShortDescription("chest")
        ob.SetLongDescription("This is a chest.")
        ob.MoveTo(room)        

    def AddUser(self, user):
        if self.bodiesByUsername.has_key(user.name):
            raise RuntimeError("User", user.name, "already present")

        body = Body(self, user)
        self.bodiesByUsername[user.name] = body
        user.SetBody(body)

        body.MoveTo(self.startingRoom)
        body.SetName(user.name.capitalize())

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
