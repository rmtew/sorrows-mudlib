
import math
from mudlib import DeveloperCommand

class CHeight(DeveloperCommand):
    __verbs__ = [ 'cheight' ]

    def Run(self, arg):
        cline = arg[0]
        if not len(cline):
            return self.shell.user.Tell('cheight <x> <y> <z>')
        try:
            coords = [ float(x.strip()) for x in cline.split(' ') ]
        except ValueError:
            return self.shell.user.Tell('Expected float arguments, got something else: '+ str(arg))

        w = sorrows.world.example
        height = w.GetSurfaceHeight(coords)
        if height >= w.seaLevel:
            self.shell.user.Tell('Result: %f (land)' % height)
        else:
            self.shell.user.Tell('Result: %f (water)' % height)
