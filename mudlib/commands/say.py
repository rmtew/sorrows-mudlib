from mudlib import Command

class Say(Command):
    __verbs__ = [ 'say' ]

    def Run(self, verb, argString):
        if len(argString):
            for user in self.shell.user.connection.manager.room.players:
                prefix = self.shell.user.name +' says: '
                if user == self.shell.user:
                    prefix = 'You say: '
                user.Tell(prefix + argString +'.')
        else:
            self.shell.user.Tell('Say what?.')
