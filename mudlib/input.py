from types import *

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
        from mudlib.shells import LoginShell
        self.shell = LoginShell()
        self.shell.Setup(self)

    def Release(self):
        self.user = None
        self.stack = []
        self.shell = None

    def Push(self, handler):
        if isinstance(handler, InputHandler):
            self.stack.append(handler)
        else:
            raise RuntimeError("Bad handler passed to Push", handler)

    def Pop(self):
        # The bottom of the stack is the login/creator/player shell position.
        # NOTHING ELSE should go there.  We prevent them from being removed.
        if len(self.stack) > 1:
            self.stack[-1].OnRemovalFromStack()
            self.stack.pop()

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

    def WritePrompt(self):
        prompt = self.stack[-1].prompt
        if type(prompt) is MethodType:
            prompt = apply(prompt,())
            self.user.Write(prompt)

    def ReceiveInput(self, input, bottomlevel = 0):
        if bottomlevel:
            handler = self.stack[0]
        else:
            handler = self.stack[-1]
        apply(handler.function, (input,))
        if self.user:
            self.WritePrompt()

