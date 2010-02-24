from mudlib import GameCommand

class Take(GameCommand):
    __verbs__ = [ 'get', 'take' ]

    # CMD MILESTONE 1: GET ITEM [implicitly from ground]

    @staticmethod
    def syntax_SUBJECT(context, matches):
        relevantMatches = [ match for match in matches if match.container is context.room ]
        if len(relevantMatches) == 1:
            ob = relevantMatches[0]
            ob.MoveTo(context.body)

            context.room.Message("{0.S} {0.v} {1.s}.", (context.body, context.verb), ob)
            return

        context.user.Tell("Take does not know how to handle that..")

    # CMD MILESTONE 2: GET ITEM FROM CONTAINER

    @staticmethod
    def syntax_SUBJECT_from_OBJECT(context, smatches, omatches):
        match = smatches[0]
        match.MoveTo(context.body)
        context.user.Tell("Ok.")
    
    # CMD MILESTONE 3: GET ITEM FROM PERSON
    # CMD MILESTONE 3: TAKE ITEM FROM PERSON

