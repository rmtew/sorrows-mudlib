import string
import mudlib
from mudlib import Shell, InputHandler

class PythonShell(Shell):
    def Setup(self, stack):
        Shell.Setup(self, stack)

        handler = InputHandler()
        handler.Setup(self, self.ReceiveInput, self.WritePrompt, 0)
        stack.Push(handler)

        self.globalDict = d = {}
        d["_"] = None
        d["user"] = self.user
        d["mudlib"] = mudlib
        if self.user.body is not None:
            d["body"] = self.user.body
            d["world"] = self.user.body.service
        else:
            d["body"] = d["world"] = None

        self.user.Tell('Python shell [type "exit"/"quit" to exit]:')

    def ReceiveInput(self, s):
        s = s.strip()
        # Ignore sent carriage returns.
        if len(s) == 0:
            return
        if s == "exit" or s == "quit":
            self.stack.Pop()
            return

        try:
            self.globalDict["_"] = value = eval(s, self.globalDict)
            self.user.Tell('Returns: '+ str(value))
        except:
            self.user.Tell("An exception occured ("+ s +"):")
            import sys,traceback
            tbList = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
            for tb in tbList:
                #self.user.Tell(repr(tb)#)
                for line in tb.split('\n'):
                    self.user.Tell(line +"\r")

    def WritePrompt(self):
        return '] '

