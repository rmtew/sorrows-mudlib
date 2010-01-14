import sys
import stackless
from httpserver import StacklessHTTPServer, RequestHandler

from mudlib import Service

class WWWService(Service):
    __sorrows__ = 'www'
    __optional__ = True

    def Run(self):    
        stackless.tasklet(self.RunServer)()

    def RunServer(self):
        cfg = sorrows.data.config.www

        self.LogInfo("Listening on address %s:%s", cfg.host, cfg.port)
        self.server = StacklessHTTPServer((cfg.host, cfg.getint("port")), RequestHandler)
        self.server.serve_forever()
