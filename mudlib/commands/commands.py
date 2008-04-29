from mudlib import Command

class Commands(Command):
    __verbs__ = [ 'commands' ]

    def Run(self, verb, arg):
        self.shell.user.Tell('Available commands:')
        for commandName in sorrows.commands.List():
            self.shell.user.Tell('  '+ commandName)
