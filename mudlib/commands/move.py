from mudlib import util, GameCommand

class Move(GameCommand):
    __aliases__ = util.directionAliases
    __verbs__ = list(direction for direction in util.directionAliases.itervalues())

    def syntax_(self, info):
        body = self.shell.user.GetBody()
        direction = util.ResolveDirection(info.verb)

        if body.MoveDirection(direction):
            self.shell.user.Tell(body.Look())
            self.shell.user.Tell(body.GetLocality())
            return

        self.shell.user.Tell("You can't go %s." % direction)
