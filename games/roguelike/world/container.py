from game.world import Object

class Container(Object):
    def __init__(self):
        Object.__init__(self)
    
        self.contents = []

    def AddObject(self, ob):
        self.contents.append(ob)

    def RemoveObject(self, ob):
        self.contents.remove(ob)

    def LookString(self, viewer):
        s = Object.LookString(self, viewer)
        if len(self.contents):
            contentsString = ", ".join(ob.shortDescription for ob in self.contents)
        else:
            contentsString = "Nothing"
        s += "\r\nIt contains: "+ contentsString +"."
        return s
