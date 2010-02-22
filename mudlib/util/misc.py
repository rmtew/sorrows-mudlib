directionAliases = {
    "n"  : "north",
    "s"  : "south",
    "e"  : "east",
    "w"  : "west",
    "ne" : "northeast",
    "nw" : "northwest",
    "se" : "southeast",
    "sw" : "southwest",
}

def ResolveDirection(word):
    directionName = directionAliases.get(word, None)
    if directionName is None:
        directionName = word
    return directionName
