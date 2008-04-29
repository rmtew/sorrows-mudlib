from mudlib import Command

class Rehash(Command):
    __verbs__ = [ 'rehash' ]

    def Run(self, verb, arg):
        self.shell.user.Tell('Rehashing commands..')
        sorrows.files.ReloadDirectory('commands')
