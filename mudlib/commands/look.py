from mudlib import GameCommand

class Look(GameCommand):
    __verbs__ = [ "look" ]
    __aliases__ = [ "l" ]

    def syntax_(self, info):
        body = self.shell.user.GetBody()
        self.shell.user.Tell(body.Look())
        if hasattr(body, "GetLocality"):
            self.shell.user.Tell(body.GetLocality())
