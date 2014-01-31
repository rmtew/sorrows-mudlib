import textsupport
import mudlib

class Object(mudlib.Object):
    container = None

    shortDescription = "UNDESCRIBED"
    longDescription = "THIS OBJECT IS UNDESCRIBED"
    position = None

    def __init__(self, shortDescription=None):
        super(Object, self).__init__()
        
        if shortDescription is not None:
            self.SetShortDescription(shortDescription)

    def SetShortDescription(self, shortDescription):
        self.shortDescription = shortDescription

    def GetShortDescription(self):
        return self.shortDescription

    def SetLongDescription(self, longDescription):
        self.longDescription = longDescription

    def GetLongDescription(self):
        return self.longDescription

    def LookString(self, viewer):
        return self.longDescription

    # ------------------------------------------------------------------------

    def SetPosition(self, position):
        self.position = position

    def GetPosition(self):
        return self.position

    def MoveTo(self, dest):
        if self.container:
            self.container.RemoveObject(self)

        dest.AddObject(self)
        self.container = dest
