
class Command:
    def __init__(self, shell):
        self.shell = shell

    def Release(self):
        del self.shell

    def Run(self, verb, argString):
        pass


class PlayerCommand(Command):
    pass

class GameCommand(PlayerCommand):
    def Run(self, verb, argString):
        pass
    
class DeveloperCommand(Command):
    pass
