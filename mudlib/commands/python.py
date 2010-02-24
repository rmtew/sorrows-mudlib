from mudlib import DeveloperCommand

class Python(DeveloperCommand):
    __verbs__ = [ 'python' ]

    @staticmethod
    def Run(context):
        from mudlib.shells import PythonShell
        PythonShell().Setup(context.user.inputStack)
