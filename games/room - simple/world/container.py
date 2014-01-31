import mudlib
import game.world

class Container(mudlib.Container, game.world.Object):
    verbWord = "contain"

    def LookString(self, viewer):
        s = super(Container, self).LookString(viewer)
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
        vo = game.world.ViewedObject(viewer=viewer, object=self, verb=self.verbWord)
        s += "\r\n{0.Pn} {0.v}: {1}.".format(vo, contentsString)
        return s
