from mudlib import PlayerCommand

class Who(PlayerCommand):
    __verbs__ = [ 'who' ]

    def Run(self, verb, arg):
        self.shell.user.Tell('You can see:')
        for conn in self.shell.user.connection.service.telnetConnections:
            self.shell.user.Tell('  '+ conn.user.name +'.')
