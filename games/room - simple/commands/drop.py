from mudlib import GameCommand

class Drop(GameCommand):
    __verbs__ = [ 'drop' ]
    
    # DROP ITEM [implicitly to ground]

    def syntax_SUBJECT(self, matches):
        print "DROP CALL", matches
