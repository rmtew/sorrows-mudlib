import sys, os
import stackless, socket
from httpserver import StacklessHTTPServer, RequestHandler

from mudlib import Service

class WWWService(Service):
    __sorrows__ = 'www'
    __optional__ = True

    def Run(self):    
        self.htmlPath = ""
        # self.htmlPath = os.path.join(sorrows.services.gameDataPath, "www-soiled")
        # self.htmlPath = os.path.join(sorrows.services.gameDataPath, "www-fmud")

        stackless.tasklet(self.RunServer)()
        if self.htmlPath:
            stackless.tasklet(self.ServeFlashPolicy)()

    def ServeFlashPolicy(self):
        s = open(os.path.join(self.htmlPath, "flashpolicy.xml")).read()

        listenSkt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listenSkt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listenSkt.bind(("127.0.0.1", 843))
        listenSkt.listen(5)
        while True:
            incomingSkt, clientAddress = listenSkt.accept()
            self.LogInfo("Flash policy request from %s", clientAddress)
            incomingSkt.sendall(s)
            incomingSkt.close()
            self.LogInfo("Flash policy served to %s", clientAddress)

    def RunServer(self):
        cfg = sorrows.data.config.www

        self.LogInfo("Listening on address %s:%s", cfg.host, cfg.port)
        self.server = StacklessHTTPServer((cfg.host, cfg.getint("port")), RequestHandler)

        if self.htmlPath:
            if True:
                for fileName in ("AC_OETags.js", "beep.mp3", "soiled.html", "soiled.swf", "soiled.txt"):
                    self.server.pages["/"+ fileName] = os.path.join(self.htmlPath, fileName)

            if False:
                for fileName in ("FMud.html", "FMud.swf"):
                    self.server.pages["/"+ fileName] = os.path.join(self.htmlPath, fileName)

        self.server.serve_forever()
