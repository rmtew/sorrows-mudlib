from mudlib import Command

class Shutdown(Command):
    __verbs__ = [ 'shutdown' ]

    def Run(self, verb, arg):
        if self.shell.user.name != "richard":
            self.shell.user.Tell('Access denied.')
            return
        self.shell.user.Tell('Going down maybe..')
        dispatch.ok = 0
