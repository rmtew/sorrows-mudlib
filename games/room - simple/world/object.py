import textsupport
import mudlib

class Object(mudlib.Object):
    container = None

    primaryNoun = None
    name = ""
    shortDescription = "UNDESCRIBED"
    longDescription = "THIS OBJECT IS UNDESCRIBED"

    def __init__(self, shortDescription=None):
        self.nouns = set()
        self.plurals = set()
        self.adjectives = set()

        if shortDescription is not None:
            self.SetShortDescription(shortDescription)

    def Release(self):
        if self.container:
            self.container.RemoveObject(self)
            self.container = None
        mudlib.Object.Release(self)

    def IdentifiedBy(self, noun):
        return noun in self.nouns or noun in self.plurals

    def DescribedBy(self, adjectives):
        return self.adjectives & adjectives == adjectives

    def AddNoun(self, noun, clean=False):
        if not clean:
            noun = noun.strip().lower()
        self.nouns.add(noun)
        if noun != self.name:
            plural = textsupport.pluralise(noun)
            self.plurals.add(plural)

    def AddAdjective(self, adjective):
        self.adjectives.add(adjective.strip().lower())

    def SetName(self, name):
        self.name = name.lower()
        self.shortDescription = name
        self.AddNoun(self.name, clean=True)

    def SetShortDescription(self, shortDescription):
        self.shortDescription = shortDescription

        words = self.shortDescription.lower().split(" ")

        # The last word is the noun.
        self.primaryNoun = words.pop().strip()
        self.AddNoun(self.primaryNoun, clean=True)

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
        return dest

