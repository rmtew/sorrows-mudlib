import game.world

class Container(game.world.Object):
    def __init__(self):
        game.world.Object.__init__(self)
    
        self.contents = []

    def AddObject(self, ob):
        self.contents.append(ob)

    def RemoveObject(self, ob):
        self.contents.remove(ob)

    def LookString(self, viewer):
        s = game.world.Object.LookString(self, viewer)
        if len(self.contents):
            contentsString = ""
            for idx, ob in enumerate(self.contents):
                if len(self.contents) > 1 and idx == len(self.contents)-1:
                    contentsString += " and "
                elif idx > 0:
                    contentsString += ", "
                contentsString += "{0.s}".format(game.world.ViewedObject(viewer=viewer, object=ob))
        else:
            contentsString = "Nothing"
        s += "\r\nIt contains: "+ contentsString +"."
        return s
