from mudlib import GameCommand

class Say(GameCommand):
    __verbs__ = [ 'say' ]

    def syntax_STRING(self, info, string):
        info.room.Message("{0.S} {0.v}: {1}.", (info.body, info.verb), string)
