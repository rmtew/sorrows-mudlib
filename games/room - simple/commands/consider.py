from mudlib import GameCommand

class Consider(GameCommand):
    __verbs__ = [ 'consider' ]

    @staticmethod
    def syntax_SUBJECT(context, matches):
        for ob in matches:
            context.user.Tell("Target: %s." % ob.shortDescription)
            context.user.Tell("  Weight: %0.1f kg" % ob.GetTotalWeight())
