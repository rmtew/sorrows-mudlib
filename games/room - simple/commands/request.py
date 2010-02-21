from mudlib import GameCommand

class Request(GameCommand):
    __verbs__ = [ 'request' ]

    # CMD MILESTONE 3: REQUEST ITEM FROM PERSON

    def Run(self, verb, arg):
        self.shell.user.Tell("TRIED TO REQUEST SOMETHING")
