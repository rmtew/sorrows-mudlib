from mudlib import GameCommand

class Drop(GameCommand):
    __verbs__ = [ 'drop' ]
    
    # DROP ITEM [implicitly to ground]

    @staticmethod
    def syntax_SUBJECTB(context, matches):
        for ob in matches:
            ob.MoveTo(context.room)
            context.room.Message(context, "{0.S} {0.v} {1.s}.", (context.body, context.verb), ob)
