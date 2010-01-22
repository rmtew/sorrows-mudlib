from mudlib import WorldCommand

class StartCmd(WorldCommand):
    __verbs__ = [ 'start' ]

    def Run(self, verb, arg):
        body = self.shell.user.GetBody()
        if body is None:
            return self.shell.user.Tell("You do not have a presence, use the \"world\" command.")
        self.shell.user.Tell("Starting the simulation.")
        body.service.StartSimulation()
