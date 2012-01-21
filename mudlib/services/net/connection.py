import socket
from errno import EBADF

class Connection(object):
    released = False
    connected = True

    def __init__(self, _socket):
        self.socket = _socket

    def Setup(self, service, connectionID=None):
        self.service = service
        self.connectionID = connectionID

    def Release(self):
        self.released = True
        self.service = None

    def OnDisconnection(self):
        self.connected = False

    def close(self):
        self.socket.close()
        # Let ourselves know that the socket has been disconnected.
        self.OnDisconnection()

    def send(self, *args):
        try:
            return self.socket.send(*args)
        except socket.error, e:
            if e.errno == EBADF:
                return
            raise e

    def recv(self, byteCount):
        try:
            ret = self.socket.recv(byteCount)
        except socket.error, e:
            if e.errno != EBADF:
                raise e
            ret = ""

        # Detect if the socket has been disconnected and handle it if so.
        if ret == "":
            self.OnDisconnection()
        return ret
