from mudlib import GameCommand

class Give(GameCommand):
    __verbs__ = [ 'give' ]

    # CMD MILESTONE 3: GIVE ITEM TO PERSON

    def Run(self, verb, arg):
        self.shell.user.Tell("TRIED TO GIVE SOMETHING")
