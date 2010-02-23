import textsupport
from mudlib import PlayerCommand, commandLabels, commandLabelsByAccessMask

class Commands(PlayerCommand):
    __verbs__ = [ 'commands' ]

    def Run(self, verb, arg):
        commandsByAccessMask = sorrows.commands.List(self.shell.__access__)
        aliases = sorrows.commands.ListAliases(self.shell.__access__)
        write = self.shell.user.Tell

        l = []
        maxWordLength = 0
        for commandLabel, accessMask in commandLabels:
            verbs = commandsByAccessMask.get(accessMask, None)
            if verbs is not None:
                verbs = list(v for v in verbs if v not in aliases)
                verbs.sort()
                maxWordLength = max(maxWordLength, max(len(s) for s in verbs))
                l.append((commandLabel, verbs))

        for i, (commandLabel, verbs) in enumerate(l):
            write("%s%s commands:" % ("" if i == 0 else "\r\n", commandLabel.capitalize()))
            write(textsupport.hcolumns(verbs,
                    width=self.shell.user.connection.consoleColumns,
                    columnSize=maxWordLength))
