from mudlib import GameCommand

class Drop(GameCommand):
    __verbs__ = [ 'drop' ]
    
    # DROP ITEM [implicitly to ground]

    @staticmethod
    def syntax_SUBJECT(context, matches):
        relevantMatches = [ match for match in matches if match.container is context.body ]
        if len(relevantMatches) == 1:
            ob = relevantMatches[0]
            ob.MoveTo(context.room)

            context.room.Message("{0.S} {0.v} {1.s}.", (context.body, context.verb), ob)
            return

        context.user.Tell("Drop does not know how to handle that..")
