from mudlib import GameCommand

class Take(GameCommand):
    __verbs__ = [ 'get', 'take' ]

    # CMD MILESTONE 1: GET ITEM [implicitly from ground]

    @staticmethod
    def syntax_SUBJECTR(context, matches):
        for ob in matches:
            ob.MoveTo(context.body)
            context.room.Message(context, "{0.S} {0.v} {1.s}.", (context.body, context.verb), ob)

    # CMD MILESTONE 2: GET ITEM FROM CONTAINER

    @staticmethod
    def syntax_SUBJECT_from_OBJECT(context, smatches, omatches):
        for ob in smatches:
            container = ob.container
            ob.MoveTo(context.body)
            context.room.Message(context, "{0.S} {0.v} {1.s} from {2.s}.", (context.body, context.verb), ob, container)
    
    # CMD MILESTONE 3: GET ITEM FROM PERSON
    # CMD MILESTONE 3: TAKE ITEM FROM PERSON

