from mudlib import PlayerCommand

class Move(PlayerCommand):
    __verbs__ = [ 'n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw' ]

    def Run(self, verb, arg):
        body = self.shell.user.GetBody()
        body.MoveDirection(verb)

        self.shell.user.Tell(body.Look())
        self.shell.user.Tell(body.GetLocality())
