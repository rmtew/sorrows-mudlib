from mudlib import util, PlayerCommand

class Move(PlayerCommand):
    __aliases__ = util.directionAliases
    __verbs__ = list(direction for direction in util.directionAliases.itervalues())

    def Run(self, verb, arg):
        body = self.shell.user.GetBody()
        direction = util.ResolveDirection(verb)

        if body.MoveDirection(direction):
            self.shell.user.Tell(body.Look())
            self.shell.user.Tell(body.GetLocality())
            return

        self.shell.user.Tell("You can't go %s." % direction)
