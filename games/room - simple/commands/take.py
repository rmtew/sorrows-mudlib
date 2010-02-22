from mudlib import GameCommand

class Take(GameCommand):
    __verbs__ = [ 'get', 'take' ]

    # CMD MILESTONE 1: GET ITEM [implicitly from ground]

    def syntax_SUBJECT(self, matches):
        print "TAKE CALL", matches


    
    # CMD MILESTONE 2: GET ITEM FROM CONTAINER
    # CMD MILESTONE 3: GET ITEM FROM PERSON
    # CMD MILESTONE 3: TAKE ITEM FROM PERSON

