from mudlib import PlayerCommand

class Who(PlayerCommand):
    __verbs__ = [ 'who' ]

    @staticmethod
    def Run(context):
        context.user.Tell('You can see:')
        for conn in context.user.connection.service.telnetConnections:
            context.user.Tell('  '+ conn.user.name +'.')
