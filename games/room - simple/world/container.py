from game.world import Object

class Container(Object):
    def __init__(self):
        Object.__init__(self)
    
        self.contents = []

    def AddObject(self, ob):
        self.contents.append(ob)

    def RemoveObject(self, ob):
        self.contents.remove(ob)
