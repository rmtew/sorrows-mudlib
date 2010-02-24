from mudlib import GameCommand

class Look(GameCommand):
    __verbs__ = [ "look" ]
    __aliases__ = [ "l" ]

    @staticmethod
    def syntax_(context):
        context.user.Tell(context.room.LookString(context.body))

    @staticmethod
    def syntax_SUBJECT(context, smatches):
        context.user.Tell(smatches[0].LookString(context.body))
