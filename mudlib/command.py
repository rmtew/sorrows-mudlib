class Command:
    def __init__(self, shell):
        self.shell = shell

    def Release(self):
        del self.shell

    def Run(self, verb, argString):
        pass
