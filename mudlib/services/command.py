import types
from mudlib import Service, Command

class CommandService(Service):
    __sorrows__ = 'commands'

    def Run(self):
        self.verbs = {}

        from mudlib import commands
        for k, v in commands.__dict__.iteritems():
            if type(v) is not types.ClassType or v is Command or not issubclass(v, Command):
                continue
            for verb in getattr(v, '__verbs__', []):
                if self.verbs.has_key(verb):
                    self.LogWarning('Duplicate command', verb)
                    continue
                self.verbs[verb] = v

    def RegisterDynamicCommand(self, verb, handler):
        self.verbs[verb] = handler

    def Execute(self, shell, verb, argString):
        if self.verbs.has_key(verb):
            cmd = self.verbs[verb](shell)
            try:
                cmd.Run(verb, argString)
            finally:
                cmd.Release()
            return 1
        return 0

    def List(self):
        return self.verbs.keys()
