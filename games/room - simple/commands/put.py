from mudlib import GameCommand

class Put(GameCommand):
    __verbs__ = [ 'put' ]
    
    # CMD MILESTONE 2: PUT ITEM IN CONTAINER

    def Run(self, verb, arg):
        self.shell.user.Tell("TRIED TO PUT SOMETHING")
