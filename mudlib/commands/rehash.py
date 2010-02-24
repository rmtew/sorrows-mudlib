from mudlib import DeveloperCommand

class Rehash(DeveloperCommand):
    __verbs__ = [ 'rehash' ]

    @staticmethod
    def Run(context): 
        oldCommands = sorrows.commands.List(context.userAccessMask)
        sorrows.commands.Rehash()
        newCommands = sorrows.commands.List(context.userAccessMask)

        return
        """
        changes = True
        # Notify the user about detected command removals.
        for s in oldCommands - newCommands:
            context.user.Tell('Removed: %s' % s)
        else:
            changes = False
        # Notify the user about newly detected commands.
        for s in newCommands - oldCommands:
            context.user.Tell('Added: %s' % s)
        else:
            changes = False
        # Notify the user if no changes have been detected.
        if not changes:
            context.user.Tell('No commands added or removed.')
        """
