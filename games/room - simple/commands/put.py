from mudlib import GameCommand

class Put(GameCommand):
    __verbs__ = [ 'put' ]
    
    # CMD MILESTONE 2: PUT ITEM IN CONTAINER

    @staticmethod
    def syntax_SUBJECT_in_OBJECT(context, smatches, omatches):
        container = omatches[0]
        for ob in smatches:
            ob.MoveTo(container)
        context.user.Tell("Ok.")
