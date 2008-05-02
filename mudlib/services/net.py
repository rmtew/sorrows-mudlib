# TODO: The socket polling is a bit of a mess.
#       The registration of connections with the net service added in order to
#       get the external intermud service working on it seems a bit hodgepodge.
#       ?

import uthread, asyncore, socket
from mudlib.services.net import TelnetConnection, MudConnection, Connection
from mudlib import User
from mudlib import Service


class NetworkService(Service):
    __sorrows__ = 'net'
    __listenevents__ = [ 'OnServicesStarted' ]

    def Run(self):
        self.telnetConnections = []
        self.nextConnectionID = 1
        
    def OnServicesStarted(self):
        uthread.new(self.ManagePump)
        
        config = sorrows.data.config.net
        host, port = config.host, config.getint("port")

        listenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listenSocket.wrap_accept_socket = self.WrapSocket
        listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listenSocket.bind((host, port))
        listenSocket.listen(5)
        uthread.new(self.AcceptTelnetConnections, listenSocket)

    def WrapSocket(self, newSocket):
        return TelnetConnection(newSocket)

    def AcceptTelnetConnections(self, listenSocket):
        while self.IsRunning():
            import stackless
            currentSocket, clientAddress = listenSocket.accept()
            currentSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            from mudlib.services.net import TelnetConnection
            connection = TelnetConnection(currentSocket)
            connection.Setup(self, self.nextConnectionID, echo=False)
            connection.clientAddress = clientAddress
            print "Telnet connection: #%s Address=%s" % (self.nextConnectionID, clientAddress)
            # Store this for our printing convenience.
            self.telnetConnections.append(connection)
            self.nextConnectionID += 1
        
    def ManagePump(self):
        while self.IsRunning():
            asyncore.poll(0.05)
            uthread.BeNice()

    def OnServerDisconnection(self, connection):
        print "OnServerDisconnection", connection

    def OnTelnetDisconnection(self, connection):
        print "Telnet disconnection: #%s Address=%s" % (connection.connectionID, connection.clientAddress)
        self.telnetConnections.remove(connection)
        connection.Release()
