from mudlib import GameCommand

class Inventory(GameCommand):
    __verbs__ = [ 'inventory' ]
    __aliases__ = [ 'i', 'inv' ]

    @staticmethod
    def syntax_(context):
        context.user.Tell("You see:")
        if len(context.body.contents):
            for ob in context.body.contents:
                context.user.Tell("  %s." % ob.shortDescription)
        else:
            context.user.Tell("  Nothing.")
