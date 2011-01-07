#try:
#    from cycapi import CycConnection
#    skip = False
#except ImportError, e:
#    skip = True

if False: # not skip:
    import socket
    import stackless
    from mudlib import Service

    # Wrap the CycConnection class to support our stackless wrapper.
    class MudCycConnection(CycConnection.CycConnection):
        def initializeApiConnections(self):
            if self.communicationMode == CycConnection.ASCII_MODE:
                asciiSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connection = sorrows.net.RegisterConnection("TEXT", asciiSocket)
                connection.Setup(sorrows.opencyc)
                self.asciiSocket = connection
                self.asciiSocket.connect((self.hostName, self.asciiPort))

    class OpenCycService(Service):
        __sorrows__ = 'opencyc'

        def Run(self):
            self.LogInfo("Connecting to localhost:3600")
            self.connection = None
            self.cycConnection = MudCycConnection('127.0.0.1', 3600)

        # -----------------------------------------------------------------------
        # OnStop - Event indicating the service is being stopped
        # -----------------------------------------------------------------------
        def OnStop(self):
            if self.connection is not None:
                sorrows.net.DeregisterConnection(self.connection)
            self.LogInfo("Disconnected.")

        # -----------------------------------------------------------------------
        # OnConnected - A socket connected
        # -----------------------------------------------------------------------
        def OnConnected(self, connection):
            self.LogInfo("Connected.")
            self.connection = connection

            stackless.tasklet(self.ManageConnection)()

        # -----------------------------------------------------------------------
        # OnDisconnection - A socket disconnected.
        # -----------------------------------------------------------------------
        def OnDisconnection(self, connection):
            self.LogInfo("OnDisconnection")
            self.connection = None
            if self.IsStopping():
                self.LogInfo("OnDisconnection/stopping %s", connection)
            sorrows.net.DeregisterConnection(connection)

        def ManageConnection(self):
            s = "(fi-ask '(#$isa #$Person ?WHAT) '#$InferencePSC)\r\n"
            ret = self.cycConnection.converse(s)
            self.LogInfo("RCVD %s", ret)

#            while self.connection.connected:
                #print "OPENCYC: ManageConnection - reading"
                #x = self.connection.read()
                #print "OPENCYC: ManageConnection - read", x
