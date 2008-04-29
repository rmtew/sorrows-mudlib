from mudlib import Command

class Python(Command):
    __verbs__ = [ 'python' ]

    def Run(self, verb, arg):
        if self.shell.user.name != "richard":
            self.shell.user.Tell('Access denied.')
            return

        from mudlib.shells import PythonShell
        PythonShell().Setup(self.shell.stack)
