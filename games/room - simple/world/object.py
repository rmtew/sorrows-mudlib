import mudlib

class Object(mudlib.Object):
    container = None

    primaryNoun = None
    shortDescription = "UNDESCRIBED"
    longDescription = "THIS OBJECT IS UNDESCRIBED"

    def __init__(self, shortDescription=None):
        self.nouns = set()
        self.adjectives = set()

        if shortDescription is not None:
            self.SetShortDescription(shortDescription)

    def AddNoun(self, noun):
        self.nouns.add(noun.strip().lower())

    def AddAdjective(self, adjective):
        self.adjectives.add(adjective.strip().lower())

    def SetShortDescription(self, shortDescription):
        self.shortDescription = shortDescription

        words = self.shortDescription.lower().split(" ")

        # The last word is the noun.
        self.primaryNoun = words.pop().strip()
        self.nouns.add(self.primaryNoun)

        for word in words:
            self.adjectives.add(word.strip())

    def GetShortDescription(self):
        return self.shortDescription

    def SetLongDescription(self, longDescription):
        self.longDescription = longDescription

    def GetLongDescription(self):
        return self.longDescription

    def LookString(self, viewer):
        return self.longDescription

    # ------------------------------------------------------------------------

    def MoveTo(self, dest):
        if self.container:
            self.container.RemoveObject(self)

        dest.AddObject(self)
        self.container = dest

