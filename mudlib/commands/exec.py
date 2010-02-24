
import math
from mudlib import DeveloperCommand
import mudlib

class ExecCommand(DeveloperCommand):
    __verbs__ = [ 'exec' ]

    @staticmethod
    def Run(context):
        raw = context.argString.strip()
        s = "return "
        if raw.startswith(s):
            raw = raw[s:]
        if not len(raw):
            return context.user.Tell('Usage: exec <python code>')

        locs = {
            "mudlib" : mudlib,
            "user": context.user,
            "body": context.body,
        }
        value = eval(raw, {}, locs)
        context.user.Tell('Result: %s' % str(value))
