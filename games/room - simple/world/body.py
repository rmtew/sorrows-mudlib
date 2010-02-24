from game.world import Container

class Body(Container):
    def __init__(self, service, user):
        Container.__init__(self)

        self.service = service
        self.user = user

    def Release(self):
        Container.Release(self)

    def MoveDirection(self, verb):
        destinationRoom = self.container.GetExitRoom(verb)
        if destinationRoom:    
            self.MoveTo(destinationRoom)
            return True
        return False

