import textsupport
from mudlib import PlayerCommand, commandLabels, commandLabelsByAccessMask

class Commands(PlayerCommand):
    __verbs__ = [ 'commands' ]

    @staticmethod
    def Run(context):
        commandsByAccessMask = sorrows.commands.List(context.userAccessMask)
        aliases = sorrows.commands.ListAliases(context.userAccessMask)
        write = context.user.Tell

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
                    width=context.user.connection.consoleColumns,
                    columnSize=maxWordLength))
