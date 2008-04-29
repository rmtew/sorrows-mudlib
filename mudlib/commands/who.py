from mudlib import Command

class Who(Command):
    __verbs__ = [ 'who' ]

    def Run(self, verb, arg):
        self.shell.user.Tell('You can see:')
        for conn in self.shell.user.connection.service.telnetConnections:
            self.shell.user.Tell('  '+ conn.user.name +'.')
