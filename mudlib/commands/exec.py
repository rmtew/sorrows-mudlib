
import math
from mudlib import DeveloperCommand
import mudlib

class ExecCommand(DeveloperCommand):
    __verbs__ = [ 'exec' ]

    def Run(self, verb, arg):
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
