from mudlib import GameCommand

class Take(GameCommand):
    __verbs__ = [ 'get', 'take' ]

    # CMD MILESTONE 1: GET ITEM [implicitly from ground]

    def syntax_SUBJECT(self, info, matches):
        relevantMatches = [ match for match in matches if match.container is info.room ]
        if len(relevantMatches) == 1:
            ob = relevantMatches[0]
            ob.MoveTo(info.body)
            info.room.Message("{0.S} {0.v} {1.s}.", (info.body, info.verb), ob)
            return

        print "UNHANDLED SITUATION", matches


    
    # CMD MILESTONE 2: GET ITEM FROM CONTAINER
    # CMD MILESTONE 3: GET ITEM FROM PERSON
    # CMD MILESTONE 3: TAKE ITEM FROM PERSON

