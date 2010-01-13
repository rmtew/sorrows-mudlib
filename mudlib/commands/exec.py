
import math
from mudlib import Command
import mudlib

class ExecCommand(Command):
    __verbs__ = [ 'exec' ]

    def Run(self, verb, arg):
        if True or self.shell.user.name != "donky":
            self.shell.user.Tell('Access denied.')
            return

        raw = arg.strip()
        s = "return "
        if raw.startswith(s):
            raw = raw[s:]
        if not len(raw):
            return self.shell.user.Tell('Syntax: exec <python code>')
        locs = {
            "mudlib" : mudlib,
            "user": self.shell.user,
            "body": self.shell.user.GetBody(),
        }
        value = eval(raw, {}, locs)
        self.shell.user.Tell('Result: %s' % str(value))
