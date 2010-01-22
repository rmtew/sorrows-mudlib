from mudlib import DeveloperCommand

class Python(DeveloperCommand):
    __verbs__ = [ 'python' ]

    def Run(self, verb, arg):
        from mudlib.shells import PythonShell
        PythonShell().Setup(self.shell.stack)
