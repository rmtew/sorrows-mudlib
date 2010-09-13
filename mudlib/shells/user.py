import string
from mudlib import Shell, InputHandler, COMMAND_PLAYER, COMMAND_GAME, COMMAND_DEVELOPER

##            if verb == "tell":
##                bits = self.arg.split(' ')
##                lname = bits[0].lower()
##                for user in self.user.connection.manager.room.players:
##                    if user.name.lower() == lname:
##                        user.Tell(self.user.name +' tells you: '+ ''.join(bits[1:]))
##                        self.user.Tell('You tell '+ user.name +': '+ ''.join(bits[1:]))
##                        return
##                self.user.Tell('There is no "'+ lname +'" logged in.')

##                for user in self.user.connection.manager.room.players:
##                    prefix = self.user.name +' leaves '
##                    if user == self.user:
##                        prefix = 'You leave '
##                    user.Tell(prefix +'the game.')
##                raise QuitException()

class GameShell(Shell):
    __access__ = COMMAND_PLAYER | COMMAND_GAME

    def Setup(self, stack):
        Shell.Setup(self, stack)

        handler = InputHandler()
        handler.Setup(self, self.ReceiveInput, self.WritePrompt, 0)

        self.stack.SetShell(handler)

        # Place the newly connected user in the game world.
        sorrows.world.AddUser(self.user)

        self.currentDirectory = (None, None) # parent, current
        
        if self.stack.stack[-1] is handler:
            self.user.Tell('You are logged in as "'+ self.user.name +'".')

    def OnRemovalFromStack(self):
        Shell.OnRemovalFromStack(self)

    def ExecuteCommand(self):
        # Ignore sent carriage returns.
        if len(self.raw) == 0:
            return

        try:
            verb = string.lower(self.verb)
            if verb == "quit":
                self.user.ManualDisconnection()
            elif not self._ExecuteCommand(verb, self.arg):
                self.user.Tell('What?')
        except Exception:
            self.user.Tell("An exception occured.")
            import sys,traceback
            tbList = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
            for tb in tbList:
                for line in tb.split('\n'):
                    self.user.Tell(line +"\r")

    def _ExecuteCommand(self, verb, argString):
        return sorrows.commands.Execute(self, verb, argString, self.__access__)

    def WritePrompt(self):
        return '> '

class DeveloperGameShell(GameShell):
    __access__ = GameShell.__access__ | COMMAND_DEVELOPER
