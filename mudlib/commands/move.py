from mudlib import GameCommand

class Move(GameCommand):
    __verbs__ = [ 'n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw' ]

    def Run(self, verb, arg):
        body = self.shell.user.GetBody()
        if body is None:
            return self.shell.user.Tell("You do not have a presence, use the \"world\" command.")
        body.MoveDirection(verb)
        self.shell.user.Tell(body.Look())
        self.shell.user.Tell(body.GetLocality())
