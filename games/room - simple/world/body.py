from game.world import Container

class Body(Container):
    def __init__(self, service, user):
        Container.__init__(self)

        self.service = service
        self.user = user

    def Release(self):
        Container.Release(self)

    def Look(self):
        if not self.container:
            return "You are nowhere"
    
        s = self.container.shortDescription +"\r\n"
        s += self.container.longDescription

        if len(self.container.contents):
            print self.container.contents
            s += "\r\nYou can see: "+ ", ".join(ob.shortDescription for ob in self.container.contents) +"."

        return s

    def GetLocality(self):
        if self.container:
            exitNames = self.container.GetExits()
            exitNames.sort()

            if len(exitNames):
                s = ", ".join(exitNames)
            else:
                s = "None"
        else:
            s = "There is nowhere to go."

        return "Exits: "+ s

    def MoveDirection(self, verb):
        destinationRoom = self.container.GetExitRoom(verb)
        if destinationRoom:    
            self.user.body.MoveTo(destinationRoom)
            return True
        return False

