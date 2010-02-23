import copy
import pysupport
from mudlib import Service, GameCommand, CommandInfo

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
                
        self.syntaxByCommand[commandName] = patterns

    def ExecuteGameCommand(self, command, verb, argString):
        """
        Called by the GameCommand class to handle parsing the arguments that
        were passed to the class, and invoking the correct syntax handler for
        those arguments passing it the resolved objects that were referred to.
        """

        info = CommandInfo()
        info.verb = verb
        info.argString = argString
        info.user = command.shell.user
        info.body = info.user.body
        info.room = info.body.container

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

        commandName = command.__class__.__name__
        for funcName, tokens in self.syntaxByCommand[commandName]:
            args = [ info ]

            if len(tokens) > 1:
                self.LogError("%s.%s had too many tokens %s", commandName, funcName, tokens)
                continue

            # Works for no tokens and 1 tokens.

            if len(tokens) == 1:
                # Incorrect arguments automatically generates a usage string.
                if argString == "":
                    info.user.Tell("Usage: %s %s" % (verb, tokens_to_string(tokens)))
                    return
            
                if tokens[0] == "SUBJECT":
                    words = [ s.strip().lower() for s in argString.split(" ") ]
                    noun = words.pop()
                    adjectives = set(words)

                    matches = []
                    # Naively look inside the room and what is held or carried for now.
                    for ob in info.room.contents:
                        if noun.lower() in ob.nouns and ob.adjectives & adjectives == adjectives:
                            matches.append(ob)
                    for ob in info.body.contents:
                        if noun.lower() in ob.nouns and ob.adjectives & adjectives == adjectives:
                            matches.append(ob)

                    if not len(matches):
                        info.user.Tell("You cannot find any %s." % argString)
                        return

                    args.append(matches)
                elif tokens[0] == "STRING":
                    args.append(argString)

            func = getattr(command, funcName)
            func(*args)
            return
