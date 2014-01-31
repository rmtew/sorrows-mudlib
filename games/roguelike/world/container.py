import mudlib
import game.world

class Container(mudlib.Container, game.world.Object):
    def LookString(self, viewer):
        s = Object.LookString(self, viewer)
        if len(self.contents):
            contentsString = ", ".join(ob.shortDescription for ob in self.contents)
        else:
            contentsString = "Nothing"
        s += "\r\nIt contains: "+ contentsString +"."
        return s
