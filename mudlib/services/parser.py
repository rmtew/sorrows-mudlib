import copy
import pysupport
from mudlib import Service, GameCommand

class ParserService(Service):
    __sorrows__ = 'parser'

    def Run(self):
        self.syntaxByCommand = {}

        # We start too late to have received ClassCreation events for existing
        # commands.  So we need to manually locate and process them.
        for class_ in pysupport.FindClassSubclasses(GameCommand):
            self.ProcessGameCommandClass(class_)

    # ------------------------------------------------------------------------

    def event_ClassCreation(self, namespace, className, class_):
        """
        When a developer programming against the running framework saves a
        file with a newly created class inside it, this event occurs for that
        class.
        """
    
        if class_ is not GameCommand and issubclass(class_, GameCommand):
            self.ProcessGameCommandClass(class_)

    def event_ClassUpdate(self, class_):
        """
        When a developer programming against the running framework saves a
        file with a existing class inside it, this event occurs for each class.
        """

        if class_ is not GameCommand and issubclass(class_, GameCommand):
            self.ProcessGameCommandClass(class_)

    # ------------------------------------------------------------------------

    def ProcessGameCommandClass(self, class_):
        """
        Given a class, this method locates the specially named syntax handlers
        and tokenises what syntax they handle from their function name.
        """

        commandName = class_.__name__

        def Weighting(tokenEntry):
            """ More complex syntax handled first. """
            weight = -(len(tokenEntry[1]) * 10)
            if tokens[0] != "STRING":
                weight -= 1
            return weight

        patterns = []
        for k, v in class_.__dict__.iteritems():
            if k.startswith("syntax_"):
                tokens = []
                syntaxText = k[7:]

                if syntaxText != "":
                    while syntaxText.find("__") != -1:
                        syntaxText = syntaxText.replace("__", "_")

                    tokens = syntaxText.split("_")

                patterns.append((k, tokens))

        patterns.sort(lambda x, y: cmp(Weighting(x), Weighting(y)))

        # Sorting order:
        # - Longer lengths of tokens.
        # - Objects.
        # - Strings.
                
        self.syntaxByCommand[commandName] = patterns

    def ExecuteGameCommand(self, context):
        """
        Called by the GameCommand class to handle parsing the arguments that
        were passed to the class, and invoking the correct syntax handler for
        those arguments passing it the resolved objects that were referred to.
        """

        def tokens_to_string(tokens):
            newTokens = copy.copy(tokens)
            for i, token in enumerate(tokens):
                if token.upper() == token:
                    if token == "SUBJECT":
                        token = "OBJECT"
                    if token == "STRING":
                        token = "TEXT"
                    newTokens[i] = "<%s>" % token.lower()
            return " ".join(newTokens)

        from game.world import Container

        commandName = context.commandClass.__name__
        argString = context.argString
        failures = []
        for funcName, tokens in self.syntaxByCommand[commandName]:
            args = [ context ]

            def MatchObjects(context, string, *containers):
                words = [ s.strip().lower() for s in string.split(" ") ]
                noun = words.pop()
                adjectives = set(words)

                matches = []
                # Naively look inside the room and what is held or carried for now.
                for container in containers:
                    for ob in container.contents:
                        if noun.lower() in ob.nouns and ob.adjectives & adjectives == adjectives:
                            matches.append(ob)
                return matches

            if len(tokens) == 1:
                # Incorrect arguments automatically generates a usage string.
                if argString == "":
                    failures.append((tokens, ""))
                    continue
            
                if tokens[0] == "SUBJECT":
                    matches = MatchObjects(context, argString, context.room, context.body)
                    if not len(matches):
                        failures.append((tokens, "You cannot find any %s." % argString))
                        continue
                    if len(matches) > 1:
                        failures.append((tokens, "Which %s?" % argString))
                        continue

                    args.append(matches)
                elif tokens[0] == "STRING":
                    args.append(argString)
            elif len(tokens) == 3:
                preposition = tokens[1]
                if preposition.lower() != preposition:
                    continue

                substring = " %s " % preposition
                idx = argString.find(substring)
                if idx == -1:
                    continue
                
                subjectString = argString[:idx]
                objectString = argString[idx+len(substring):]

                omatches = MatchObjects(context, objectString, context.room, context.body)
                if len(omatches) == 0:
                    failures.append((tokens, "You cannot find any %s." % objectString))
                    continue
                    
                ocontainers = [ context.body ]
                if preposition in [ "from", "in" ]:
                    omatches = [ ob for ob in omatches if isinstance(ob, Container) ]
                    if len(omatches) == 0:
                        failures.append((tokens, "You cannot find any %s." % objectString))
                        continue
                    if len(omatches) > 1:
                        failures.append((tokens, "Which %s?" % objectString))
                        continue

                    if preposition == "from":
                        ocontainers = omatches

                smatches = MatchObjects(context, subjectString, *ocontainers)
                if len(smatches) == 0:
                    failures.append((tokens, "You cannot find any %s." % subjectString))
                    continue
                
                args.append(smatches)
                args.append(omatches)
            elif len(tokens) == 0:
                if len(argString) > 0:
                    failures.append((tokens, "You cannot find any %s." % argString))
                    continue
            else:
                context.user.Tell("Case %d: no handling for %s" % (len(tokens), funcName))
                continue

            getattr(context.commandClass, funcName)(*args)
            break
        else:
            if len(failures):
                failureMessage = failures[0][-1]
                context.user.Tell(failureMessage)
            else:
                context.user.Tell("Unexpected command failure.")

