from mudlib import Command

class Python(Command):
    __verbs__ = [ 'python' ]

    def Run(self, verb, arg):
        # if self.shell.user.name != "richard":
        # If you enable this, you might want to make sure your MUD is not on the net.
        self.shell.user.Tell('Access denied.')
        return

        from mudlib.shells import PythonShell
        PythonShell().Setup(self.shell.stack)
