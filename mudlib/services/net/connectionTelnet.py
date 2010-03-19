import stackless, uthread, miniboa.telnetnegotiation
from mudlib.services.net import Connection
from mudlib import User

class TelnetConnection(Connection):
    def Setup(self, service, connectionID, echo=False):
        Connection.Setup(self, service, connectionID)

        self.passwordMode = False

        self.echo = echo
        self.consoleColumns = 80
        self.consoleRows = 24

        self.optionEcho = False
        self.optionLineMode = True
        self.readBufferString = ""

        # -- state --
        self.telneg = miniboa.telnetnegotiation.TelnetNegotiation()

        def send_cb(data):
            service.LogDebug("SEND(%s)%s%s", self.user.name, self.clientAddress, [ord(c) for c in data])
            self.send(data)
        self.telneg.set_send_cb(send_cb)

        def compress2_cb(flag):
            service.LogDebug("COMPRESS2(%s)%s[%s]", self.user.name, self.clientAddress, flag)
            self.compress2 = flag
        self.telneg.set_compress2_cb(compress2_cb)

        def echo_cb(flag):
            service.LogDebug("ECHO(%s)%s[%s]", self.user.name, self.clientAddress, flag)
            self.echo = flag
        self.telneg.set_echo_cb(echo_cb)

        def terminal_type_cb(data):
            service.LogDebug("TERMINAL TYPE(%s)%s[%s]", self.user.name, self.clientAddress, data)
        self.telneg.set_terminal_type_cb(terminal_type_cb)

        def terminal_type_selection_cb(termTypes):
            service.LogDebug("TERMINAL TYPES(%s)%s[%s]", self.user.name, self.clientAddress, termTypes)
            if "ansi" in termTypes:
                return "ansi"
            return termTypes[0]
        self.telneg.set_terminal_type_selection_cb(terminal_type_selection_cb)

        def terminal_size_cb(rows, columns):
            service.LogDebug("TERMINAL SIZE(%s)%s[%s]", self.user.name, self.clientAddress, str((rows, columns)))
            self.consoleRows = rows
            self.consoleColumns = columns
            # TODO: This callback needs to be done cleanly.
            handler = self.user.inputstack.stack[-1]
            if hasattr(handler.shell, "OnTerminalSizeChanged"):
                handler.shell.OnTerminalSizeChanged(rows, columns)
        self.telneg.set_terminal_size_cb(terminal_size_cb)

        self.user = User(self, "login")
        self.user.SetupInputStack()

        uthread.new(self.ManageConnection)

    def ManageConnection(self):
        while not self.released:
            if not self._ManageConnection():
                break

    def _ManageConnection(self):
        if self.optionLineMode:
            input = self.readline()
        else:
            input = self.read(65536)
        if input is None:
            return False
        try:
            self.user.ReceiveInput(input)
        except Exception:
            self.service.LogException("Error dispatching input")
        return True

    def OnDisconnection(self):
        # Notify the service of the disconnection.
        self.user.OnTelnetDisconnection()
        self.user = None

        self.service.OnTelnetDisconnection(self)

    def SetPasswordMode(self, flag):
        self.passwordMode = flag

    def read(self, bytes):
        s = self.recv(65536)
        if s == "":
            return None

        buf = ""
        for s in self.telneg.feed(s):
            buf += s
        return buf

    # -----------------------------------------------------------------------
    # readline
    # -----------------------------------------------------------------------
    def readline(self):
        buf = self.readBufferString

        while True:
            # We need to handle all the different line endings which clients may send:
            #   \r  \r\n  \n
            ret = ""
            rIdx = buf.find('\r')
            if rIdx == -1:
                nIdx = buf.find('\n')
                if nIdx > -1:
                    ret = buf[:nIdx]
                    self.readBufferString = buf[nIdx+1:]
            else:
                ret = buf[:rIdx]
                if len(buf) > rIdx+1 and buf[rIdx+1] == '\n':
                    self.readBufferString = buf[rIdx+2:]
                else:
                    self.readBufferString = buf[rIdx+1:]

            if len(ret):
                i = ret.find('\x08')
                while i > -1:
                    if i == 0:
                        ret = ret[1:]
                    else:
                        ret = ret[:i-1] + ret[i+1:]
                    i = ret.find('\x08', i)

                # print "INPUT-LINE", [ ord(c) for c in ret ]
                return ret

            s = self.recv(65536)
            if s == "":
                return None
            # print "INPUT-RECEIVED", [ ord(c) for c in s ]

            for s2 in self.telneg.feed(s):            
                # This is so not optimal yet, but it is correct which is good for now.
                for i, c in enumerate(s2):
                    if self.echo and not self.passwordMode:
                        if c == '\x08':
                            self.send(c +" ")
                        elif c == '\r' and i == len(s2)-1:
                            # \r and \n are expected to come in pairs.
                            # If \r is the final character, no \n was sent.
                            self.send('\n')
                        self.send(c)
                    buf += c

