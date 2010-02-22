from mudlib import PlayerCommand

class Say(PlayerCommand):
    __verbs__ = [ 'say' ]

    def Run(self, verb, argString):
        if len(argString):
            body = self.shell.user.body
            for conn in sorrows.net.telnetConnections:
                prefix = body.shortDescription +' says: '
                if conn.user is self.shell.user:
                    prefix = 'You say: '
                conn.user.Tell(prefix + argString +'.')
        else:
            self.shell.user.Tell('Say what?')
