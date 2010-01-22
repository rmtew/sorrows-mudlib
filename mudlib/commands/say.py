from mudlib import PlayerCommand

class Say(PlayerCommand):
    __verbs__ = [ 'say' ]

    def Run(self, verb, argString):
        if len(argString):
            for conn in sorrows.net.telnetConnections:
                prefix = self.shell.user.name +' says: '
                if conn.user is self.shell.user:
                    prefix = 'You say: '
                conn.user.Tell(prefix + argString +'.')
        else:
            self.shell.user.Tell('Say what?')
