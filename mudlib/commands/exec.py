
import math
from mudlib import Command

class ExecCommand(Command):
    __verbs__ = [ 'exec' ]

    def Run(self, verb, arg):
        raw = arg.strip()
        s = "return "
        if raw.startswith(s):
            raw = raw[s:]
        if not len(raw):
            return self.shell.user.Tell('Syntax: exec <python code>')
        locs = {
            "user": self.shell.user,
            "body": self.shell.user.GetBody(),
        }
        value = eval(raw, {}, locs)
        self.shell.user.Tell('Result: %s' % str(value))
