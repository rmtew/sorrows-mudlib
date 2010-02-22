from mudlib import PlayerCommand

class Look(PlayerCommand):
    __verbs__ = [ "look" ]
    __aliases__ = [ "l" ]

    def Run(self, verb, arg):
        body = self.shell.user.GetBody()
        self.shell.user.Tell(body.Look())
        if hasattr(body, "GetLocality"):
            self.shell.user.Tell(body.GetLocality())
