from mudlib import GameCommand

class Take(GameCommand):
    __verbs__ = [ 'get', 'take' ]
    __syntax__ = [
        "OBJECT",
    ]

    def syntax_SUBJECT(self, matches):
        print "XXX"
    
    # CMD MILESTONE 3: GET ITEM FROM PERSON
    # CMD MILESTONE 3: TAKE ITEM FROM PERSON
    
    # GET ITEM [implicitly from ground]
    # CMD MILESTONE 2: GET ITEM FROM CONTAINER

    def Run(self, verb, arg):
        self.shell.user.Tell("TRIED TO TAKE SOMETHING")
