class Connection:
    released = False

    def __init__(self, socket):
        self.socket = socket

    def Setup(self, service, connectionID=None):
        self.service = service
        self.connectionID = connectionID

    def Release(self):
        self.released = True
        self.service = None

    def OnDisconnection(self):
        pass

    def close(self):
        self.socket.close()
        # Let ourselves know that the socket has been disconnected.
        self.OnDisconnection()

    def send(self, *args):
        return self.socket.send(*args)

    def recv(self, byteCount):
        ret = self.socket.recv(byteCount)
        # Detect if the socket has been disconnected and handle it if so.
        if ret == "":
            self.OnDisconnection()
        return ret
