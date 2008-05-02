
import math
from mudlib import Command

class ExecCommand(Command):
    __verbs__ = [ 'exec' ]

    def Run(self, verb, arg):
        # if self.shell.user.name != "richard":
        # If you enable this, you might want to make sure your MUD is not on the net.
        self.shell.user.Tell('Access denied.')
        return

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
