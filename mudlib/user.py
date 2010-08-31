class User:
    def __init__(self, connection, name):
        self.connection = connection
        self.name = name

        self.worldServiceName = None
        self.body = None
        self.properties = {}

    def SetupInputStack(self):
        from mudlib import InputStack
        self.inputstack = InputStack()
        self.inputstack.Setup(self)
        self.inputstack.WritePrompt()

    def OnTelnetDisconnection(self):
        self.inputstack.Release()

    def __nonzero__(self):
        "The user object is still valid if its connection is."
        return not self.connection.released

    def ReceiveInput(self, s):
        self.inputstack.ReceiveInput(s)

    def Write(self, message):
        self.connection.send(message)

    def WriteLine(self, message):
        self.connection.send(message+"\r\n")

    Tell = WriteLine

    def SetBody(self, body):
        self.body = body

    def GetBody(self):
        return self.body

    @property
    def shell(self):
        return self.inputstack.GetShell()

    def ManualDisconnection(self):
        self.connection.close()
