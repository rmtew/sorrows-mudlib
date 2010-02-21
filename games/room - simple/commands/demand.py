from mudlib import GameCommand

class Demand(GameCommand):
    __verbs__ = [ 'demand' ]
    
    # CMD MILESTONE 3: DEMAND ITEM FROM PERSON

    def Run(self, verb, arg):
        self.shell.user.Tell("TRIED TO DEMAND SOMETHING")
