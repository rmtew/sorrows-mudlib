from mudlib import GameCommand

class Look(GameCommand):
    __verbs__ = [ 'l', 'look' ]

    def Run(self, verb, arg):
        body = self.shell.user.GetBody()
        if body is None:
            return self.shell.user.Tell("You do not have a presence, use the \"world\" command.")
        self.shell.user.Tell(body.Look())
        if hasattr(body, "GetLocality"):
            self.shell.user.Tell(body.GetLocality())
