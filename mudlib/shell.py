import string

class Shell:
    def Setup(self, stack):
        self.stack = stack
        self.user = stack.user

    def OnRemovalFromStack(self):
        pass

    def ReceiveInput(self, s):
        # Break the input down to the verb and arguments.
        self.raw = s
        bits = s.strip().split(" ", 1)
        if len(bits) == 1:
            self.verb = bits[0]
            self.arg = ""
        else:
            self.verb = bits[0].strip()
            self.arg = bits[1].strip()
        # Execute the commands.
        #print 'verb "%s" arg "%s"' % (self.verb, self.arg)
        result = self.ExecuteCommand()

    def ExecuteCommand(self):
        raise NameError, 'ExecuteCommand not found in the inheriting shell object'

    def Broadcast(self, msg):
        pass
