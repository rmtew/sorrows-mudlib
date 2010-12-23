from mudlib import util, GameCommand

class Move(GameCommand):
    __aliases__ = util.directionAliases
    __verbs__ = list(direction for direction in util.directionAliases.itervalues())

    @staticmethod
    def syntax_(context):
        direction = util.ResolveDirection(context.verb)

        destRoom = context.body.MoveDirection(direction)
        if destRoom is not None:
            context.user.Tell(destRoom.LookString(context.body))
        else:
            context.user.Tell("You can't go %s." % direction)
