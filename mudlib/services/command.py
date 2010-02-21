import pysupport
from mudlib import Service, PlayerCommand, DeveloperCommand

class CommandService(Service):
    __sorrows__ = 'commands'

    def Run(self):
        self.dynamicVerbs = {}

        self.Rehash()

    def Rehash(self):
        def CheckLeakedClass(class_):
            if class_.__module__ != "__builtin__":
                return False

            import gc, sys
            gc.collect()
            try:
                print "THE LEAKED CODE RELOADING CLASSES ARE BACK"
                pysupport.PrintReferrers(class_)
            except Exception:
                import traceback
                traceback.print_exc()

            return True            

        self.playerCommands = {}
        self.developerCommands = {}
        playerTuple = (pysupport.FindSubclasses(PlayerCommand), self.playerCommands, "player")
        developerTuple = (pysupport.FindSubclasses(DeveloperCommand), self.developerCommands, "developer")
        for locatedClasses, verbIndex, label in (playerTuple, developerTuple):
            self.LogInfo("%d %s commands located", len(locatedClasses), label)
            for class_ in locatedClasses:
                for verb in getattr(class_, '__verbs__', []):
                    if verbIndex.has_key(verb):
                        self.LogWarning('Duplicate command %s', verb)
                        continue

                    self.LogInfo("Command '%s' registered (%s)", verb, label)
                    verbIndex[verb] = class_

    def RegisterDynamicCommand(self, verb, handler):
        self.LogInfo("Dynamic command '%s' registered (no access levels yet)", verb)
        self.dynamicVerbs[verb] = handler

    def GetCommandClass(self, verb, accessTypes):
        class_ = None
        if "developer" in accessTypes:
            class_ = self.developerCommands.get(verb, None)
        if "player" in accessTypes:
            if class_ is None:
                class_ = self.playerCommands.get(verb, None)
            if class_ is None:
                class_ = self.dynamicVerbs.get(verb, None)
        return class_

    def Execute(self, shell, verb, argString, accessTypes):
        class_ = self.GetCommandClass(verb, accessTypes)
        if class_ is not None:
            cmd = class_(shell)
            try:
                cmd.Run(verb, argString)
            finally:
                cmd.Release()
            return True

        return False

    def List(self, shell):
        d = { }
        if "player" in shell.__access__:
            d["player"] = []
            d["player"].extend(self.playerCommands.iterkeys())
            d["player"].extend(self.dynamicVerbs.iterkeys())
        if "developer" in shell.__access__:
            d["developer"] = []
            d["developer"].extend(self.developerCommands.iterkeys())
        return d
