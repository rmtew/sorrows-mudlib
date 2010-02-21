from mudlib import GameCommand

class DropCommand(GameCommand):
    __verbs__ = [ 'drop' ]
    
    # DROP ITEM [implicitly to ground]

    def Run(self, verb, arg):
        self.shell.user.Tell("TRIED TO DROP SOMETHING")
