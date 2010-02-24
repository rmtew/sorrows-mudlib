import pysupport
from mudlib import Service, BaseCommand, commandLabelsByAccessMask, CommandContext

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

        self.commandsByAccessMask = {}
        self.verbAliases = set()
        usedVerbs = set()

        for class_ in pysupport.FindSubclasses(BaseCommand):
            accessMask = class_.__access__
            accessCommands = self.commandsByAccessMask.get(accessMask, None)
            if accessCommands is None:
                accessCommands = self.commandsByAccessMask[accessMask] = {}

            for verb in getattr(class_, '__verbs__', []):
                if verb in usedVerbs:
                    self.LogWarning('Duplicate verb %s from command %s', verb, class_)
                    continue

                self.LogInfo("Command '%s' registered (%s)", verb, commandLabelsByAccessMask[accessMask])
                accessCommands[verb] = class_

            for verb in getattr(class_, '__aliases__', []):
                if verb in usedVerbs:
                    self.LogWarning('Duplicate alias verb %s from command %s', verb, class_)
                    continue

                self.LogInfo("Command alias '%s' registered (%s)", verb, commandLabelsByAccessMask[accessMask])
                accessCommands[verb] = class_
                self.verbAliases.add(verb)

    def RegisterDynamicCommand(self, verb, handler):
        self.LogInfo("Dynamic command '%s' registered (no access levels yet)", verb)
        self.dynamicVerbs[verb] = handler

    def GetCommandClass(self, verb, userAccessMask):
        for accessMask, classByVerb in self.commandsByAccessMask.iteritems():
            if userAccessMask & accessMask == accessMask:
                class_ = classByVerb.get(verb, None)
                if class_ is not None:
                    return class_

    def Execute(self, shell, verb, argString, accessMask):
        class_ = self.GetCommandClass(verb, accessMask)
        if class_ is not None:
            context = CommandContext(class_, verb, argString, shell)
            class_.Run(context)
            return True

        return False

    def List(self, userAccessMask):
        d = {}
        for accessMask, classByVerb in self.commandsByAccessMask.iteritems():
            if userAccessMask & accessMask == accessMask:
                d[accessMask] = classByVerb.keys()
        return d

    def ListAliases(self, userAccessMask):
        aliases = set()
        for accessMask, classByVerb in self.commandsByAccessMask.iteritems():
            if userAccessMask & accessMask == accessMask:
                aliases.update(v for v in classByVerb.iterkeys() if v in self.verbAliases)
        return aliases
