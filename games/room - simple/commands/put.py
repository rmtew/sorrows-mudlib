from mudlib import GameCommand

class Put(GameCommand):
    __verbs__ = [ 'put' ]
    
    # CMD MILESTONE 2: PUT ITEM IN CONTAINER

    @staticmethod
    def syntax_SUBJECT_in_OBJECT(context, smatches, omatches):
        container = omatches[0]
        for ob in smatches:
            ob.MoveTo(container)
            context.room.Message("{0.S} {0.v} {1.s} in {2.s}.", (context.body, context.verb), ob, container)
