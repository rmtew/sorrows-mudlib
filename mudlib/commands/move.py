from mudlib import PlayerCommand

directionNames = {
    "n"  : "north",
    "s"  : "south",
    "e"  : "east",
    "w"  : "west",
    "ne" : "northeast",
    "nw" : "northwest",
    "se" : "southeast",
    "sw" : "southwest",
}

class Move(PlayerCommand):
    __verbs__ = list(directionNames)
    __verbs__.extend(directionNames.itervalues())

    def Run(self, verb, arg):
        body = self.shell.user.GetBody()
        if body.MoveDirection(verb):
            self.shell.user.Tell(body.Look())
            self.shell.user.Tell(body.GetLocality())
        else:
            directionName = directionNames.get(verb, None)
            if directionName is None:
                directionName = verb
            self.shell.user.Tell("You can't go %s." % directionName)

