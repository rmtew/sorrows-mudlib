from mudlib import WorldCommand

class Simulate(WorldCommand):
    __verbs__ = [ 'simulate' ]

    def Run(self, verb, arg):
        body = self.shell.user.GetBody()
        if body is None:
            return self.shell.user.Tell("You do not have a presence, use the \"world\" command.")
        from game.shells import SimulationShell
        SimulationShell().Setup(self.shell.stack)
