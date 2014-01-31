import types


class InputHandler:
    def Setup(self, shell, function, prompt, flags):
        self.shell = shell
        self.function = function
        self.prompt = prompt
        self.flags = flags

    def OnRemovalFromStack(self):
        self.shell.OnRemovalFromStack()
        self.shell = None


class InputStack:
    def Setup(self, user):
        self.user = user
        self.stack = []

        # Default to the login shell (they have to login first!).
        shell = None
        
        try:
            from game.shells import LoginShell
        except ImportError:
            from mudlib.shells import LoginShell
        
        shell = LoginShell()
        shell.Setup(self)

    def Release(self):
        self.user = None
        while self.Pop():
            pass

    def Push(self, handler):
        if isinstance(handler, InputHandler):
            self.stack.append(handler)
        else:
            raise RuntimeError("Bad handler passed to Push", handler)

    def Pop(self):
        # The bottom of the stack is the login/creator/player shell position.
        # NOTHING ELSE should go there.  We prevent them from being removed.
        if len(self.stack):
            if not self.user or len(self.stack) > 1:
                handler = self.stack.pop()
                handler.OnRemovalFromStack()
                return handler

    def GetHandler(self, bottomlevel=False):
        if bottomlevel:
            return self.stack[0]
        return self.stack[-1]

    def SetShell(self, handler):
        if isinstance(handler, InputHandler):
            if len(self.stack):
                # Replace the existing shell.
                self.stack[0].OnRemovalFromStack()
                self.stack[0] = handler
            else:
                # This should never happen..
                self.Push(handler)
        else:
            pass

    def GetShell(self):
        return self.GetHandler().shell

    def WritePrompt(self):
        prompt = self.stack[-1].prompt
        if type(prompt) is types.MethodType:
            self.user.Write(prompt())

    def ReceiveInput(self, input, bottomlevel=False):
        handler = self.GetHandler(bottomlevel)
        handler.function(input)
        if self.user:
            self.WritePrompt()

    def OnTerminalSizeChanged(self, columns, rows):
        for shell in self.stack:
            if hasattr(shell, "OnTerminalSizeChanged"):
                shell.OnTerminalSizeChanged(columns, rows)
