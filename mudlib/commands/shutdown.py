from mudlib import DeveloperCommand

class Shutdown(DeveloperCommand):
    __verbs__ = [ 'shutdown' ]

    @staticmethod
    def Run(context):
        if context.user.name != "richard":
            context.user.Tell('Access denied.')
            return

        context.user.Tell('Going down maybe..')
        dispatch.ok = 0
