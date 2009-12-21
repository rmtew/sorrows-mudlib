import string
from mudlib import Shell, InputHandler

class UserShell(Shell):
    def Setup(self, stack):
        Shell.Setup(self, stack)
        handler = InputHandler()
        handler.Setup(self, self.ReceiveInput, self.WritePrompt, 0)
        self.stack.SetShell(handler)
        self.currentDirectory = (None, None) # parent, current
        self.user.Tell('You are logged in as "'+ self.user.name +'".')
        # self.user.connection.manager.room.Tell(self.user.name +' enters the game.', self.user)

    def ExecuteCommand(self):
        # Ignore sent carriage returns.
        if len(self.raw) == 0:
            return
        try:
            verb = string.lower(self.verb)
##            if verb == "tell":
##                bits = self.arg.split(' ')
##                lname = bits[0].lower()
##                for user in self.user.connection.manager.room.players:
##                    if user.name.lower() == lname:
##                        user.Tell(self.user.name +' tells you: '+ ''.join(bits[1:]))
##                        self.user.Tell('You tell '+ user.name +': '+ ''.join(bits[1:]))
##                        return
##                self.user.Tell('There is no "'+ lname +'" logged in.')
            if verb == "quit":
##                for user in self.user.connection.manager.room.players:
##                    prefix = self.user.name +' leaves '
##                    if user == self.user:
##                        prefix = 'You leave '
##                    user.Tell(prefix +'the game.')
##                raise QuitException()
                self.user.ManualDisconnection()
            elif not sorrows.commands.Execute(self, verb, self.arg):
                self.user.Tell('What?')
        except Exception:
            self.user.Tell("An exception occured.")
            import sys,traceback
            tbList = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
            for tb in tbList:
                for line in tb.split('\n'):
                    self.user.Tell(line +"\r")

    def WritePrompt(self):
        return '> '

