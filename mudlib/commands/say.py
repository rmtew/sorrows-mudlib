from mudlib import GameCommand

class Say(GameCommand):
    __verbs__ = [ 'say' ]

    @staticmethod
    def syntax_STRING(context, string):
        context.room.Message(context, "{0.S} {0.v}: {1}.", (context.body, context.verb), string)
