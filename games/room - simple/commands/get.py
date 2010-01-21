from mudlib import WorldCommand

class Get(WorldCommand):
    __verbs__ = [ 'get', 'take' ]

    def Run(self, verb, arg):
        body = self.shell.user.GetBody()
        if body is None:
            return self.shell.user.Tell("You do not have a presence, use the \"world\" command.")

        self.shell.user.Tell("TRIED TO GET SOMETHING")
