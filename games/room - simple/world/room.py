import weakref

class Room:
    shortDescription = ""
    longDescription = ""

    def __init__(self):
        self.details = {}
        self.exits = weakref.WeakValueDictionary()

    def AddDetail(self, detailName, detailDescription):
        self.details[detailName] = detailDescription

    def AddExit(self, direction, room):
        self.exits[direction] = room

    def __str__(self):
        return "\r\n".join([
            self.shortDescription,
            self.longDescription,
            "",
        ])
