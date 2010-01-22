from mudlib import PlayerCommand

class Commands(PlayerCommand):
    __verbs__ = [ 'commands' ]

    def Run(self, verb, arg):
        self.shell.user.Tell('Available commands:')
        for commandName in sorrows.commands.List(self.shell):
            self.shell.user.Tell('  '+ commandName)
