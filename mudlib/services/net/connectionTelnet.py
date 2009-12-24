import stackless, uthread, miniboa.telnetnegotiation
from mudlib.services.net import Connection
from mudlib import User

class TelnetConnection(Connection):
    def Setup(self, service, connectionID, echo=False):
        Connection.Setup(self, service, connectionID)

        self.echo = echo

        self.optionEcho = False
        self.optionLineMode = True
        self.readBufferString = ""

        self.user = User(self, "login")
        uthread.new(self.ManageConnection)

        # -- state --
        self.telneg = miniboa.telnetnegotiation.TelnetNegotiation()

        def send_cb(data):
            print "SEND%s" % [ord(c) for c in data]
            self.send(data)
        self.telneg.set_send_cb(send_cb)

        def compress2_cb(flag):
            print "COMPRESS2[%s]" % flag
            self.compress2 = flag
        self.telneg.set_compress2_cb(compress2_cb)

        def echo_cb(flag):
            print "ECHO[%s]" % flag
            self.echo = flag
        self.telneg.set_echo_cb(send_cb)

        def terminal_type_cb(data):
            print "TERMINAL TYPE[%s]" % data
        self.telneg.set_terminal_type_cb(send_cb)

        def terminal_size_cb(rows, columns):
            print "TERMINAL SIZE[%s]" % str((rows, columns))
        self.telneg.set_terminal_size_cb(send_cb)

        self.telneg.request_will_compress()

    def ManageConnection(self):
        while not self.released:
            line = self.readline()
            # An empty string implies disconnection.  Ignoring that will
            # mean that the released flag should be set and we will exit.
            if line:
                # Pass on the line without the trailing CR LF.
                self.user.ReceiveInput(line[:-2])

    def OnDisconnection(self):
        # Notify the service of the disconnection.
        self.service.OnTelnetDisconnection(self)

    # -----------------------------------------------------------------------
    # readline
    # -----------------------------------------------------------------------
    def readline(self):
        buf = self.readBufferString

        while True:
            if buf.find('\r\n') > -1:
                i = buf.index('\r\n')
                ret = buf[:i+2]
                self.readBufferString = buf[i+2:]
                while '\x08' in ret:
                    i = ret.index('\x08')
                    if i == 0:
                        ret = ret[1:]
                    else:
                        ret = ret[:i-1]+ret[i+1:]
                return ret

            s = self.recv(65536)
            if s == "":
                return s

            l = list(self.telneg.feed(s))
            
            if getattr(self, "telneg_warning", False) is False:
                self.telneg_warning = True
                self.service.LogWarning("Not yet using the filtered telneg output")
            
            if self.echo:
                if s == '\x08':
                    self.send(s+" ")
                self.send(s)
            buf += s

