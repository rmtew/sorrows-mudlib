from mudlib import GameCommand

class Offer(GameCommand):
    __verbs__ = [ 'offer' ]

    # CMD MILESTONE 3: OFFER ITEM TO PERSON

    def Run(self, verb, arg):
        self.shell.user.Tell("TRIED TO OFFER SOMETHING")
