import sys
import stackless
from httpserver import StacklessHTTPServer, RequestHandler

from mudlib import Service

class WWWService(Service):
    __sorrows__ = 'www'

    def Run(self):
        address = ('127.0.0.1', 9000)
        self.LogInfo("Listening on address %s:%s", *address)

        stackless.tasklet(self.RunServer)(address)

    def RunServer(self, address):
        self.server = StacklessHTTPServer(address, RequestHandler)
        self.server.serve_forever()
