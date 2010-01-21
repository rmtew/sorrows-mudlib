import pysupport
from mudlib import Service, Command

class CommandService(Service):
    __sorrows__ = 'commands'

    def Run(self):
        self.verbs = {}
        self.dynamicVerbs = {}

        self.Rehash()

    def Rehash(self):
        l = pysupport.FindSubclasses(Command, inclusive=True)
        self.LogInfo("%d command classes located", len(l))
        
        import gc, sys
        gc.collect()
        self.verbs = {}
        for class_ in l:
            if class_.__module__ == "__builtin__":
                try:
                    print "THE LEAKED CODE RELOADING CLASSES ARE BACK"
                    pysupport.PrintReferrers(class_)
                except Exception:
                    import traceback
                    traceback.print_exc()
                continue

            for verb in getattr(class_, '__verbs__', []):
                if self.verbs.has_key(verb):
                    self.LogWarning('Duplicate command %s', verb)
                    continue

                self.LogInfo("Command '%s' registered (no access levels yet)", verb)
                self.verbs[verb] = class_

    def RegisterDynamicCommand(self, verb, handler):
        self.LogInfo("Dynamic command '%s' registered (no access levels yet)", verb)
        self.dynamicVerbs[verb] = handler

    def Execute(self, shell, verb, argString):
        class_ = self.verbs.get(verb, None)
        if class_ is None:
            class_ = self.dynamicVerbs.get(verb, None)
        if class_ is not None:
            cmd = self.verbs[verb](shell)
            try:
                cmd.Run(verb, argString)
            finally:
                cmd.Release()
            return 1
        return 0

    def List(self):
        l = self.verbs.keys()
        l.extend(self.dynamicVerbs.keys())
        return l
