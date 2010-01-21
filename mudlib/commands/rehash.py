from mudlib import Command

class Rehash(Command):
    __verbs__ = [ 'rehash' ]

    def Run(self, verb, arg):
        oldCommands = set(sorrows.commands.List())
        sorrows.commands.Rehash()
        newCommands = set(sorrows.commands.List())

        changes = True
        # Notify the user about detected command removals.
        for s in oldCommands - newCommands:
            self.shell.user.Tell('Removed: %s' % s)
        else:
            changes = False
        # Notify the user about newly detected commands.
        for s in newCommands - oldCommands:
            self.shell.user.Tell('Added: %s' % s)
        else:
            changes = False
        # Notify the user if no changes have been detected.
        if not changes:
            self.shell.user.Tell('No commands added or removed.')
