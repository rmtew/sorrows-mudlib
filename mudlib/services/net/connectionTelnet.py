import stackless, uthread
from mudlib.services.net import Connection
from mudlib import User

NUL  = chr(0)     # NULL.
LF   = chr(10)    # Line feed.
CR   = chr(13)    # Carriage return. 

BEL  = chr(7)     # Bell.
BS   = chr(8)     # Back space.
HT   = chr(9)     # Horizontal tab.
VT   = chr(11)    # Vertical tab.
FF   = chr(12)    # Form feed.

SE   = chr(240)     # End of subnegotiation parameters.
NOP  = chr(241)     # No operation.
DM   = chr(242)     # Data mark. Indicates the position of a Synch event within the data stream. This should always be accompanied by a TCP urgent notification.
BRK  = chr(243)     # Break. Indicates that the "break" or "attention" key was hit.
IP   = chr(244)     # Suspend, interrupt or abort the process to which the NVT is connected.
AO   = chr(245)     # Abort output. Allows the current process to run to completion but do not send its output to the user.
AYT  = chr(246)     # Are you there. Send back to the NVT some visible evidence that the AYT was received.
EC   = chr(247)     # Erase character. Delete last preceding undeleted character from the data stream.
EL   = chr(248)     # Erase line. Delete characters from the data stream back to but not including CRLF.
GA   = chr(249)     # Go ahead. Used, under certain circumstances, to tell the other end that it can transmit.
SB   = chr(250)     # Subnegotiation of the indicated option follows.
WILL = chr(251)     # Indicates the desire to begin performing, or confirmation that you are now performing, the indicated option.
WONT = chr(252)     # Indicates the refusal to perform, or confirmation that you are performing, the indicated option.
DO   = chr(253)     # Indicates the request that the other party perform, or confirmation that you are expecting the other party to perform, the indicated option.
DONT = chr(254)     # Indicates the demand that the other party stop performing, or confirmation that you are no longer expecting the other party to perform, the indicated option.
IAC  = chr(255)     # Interpret as command.

OPTION_ECHO                     = 1
OPTION_SUPPRESS_GO_AHEAD        = 3
OPTION_STATUS                   = 5
OPTION_TIMING_MARK              = 6
OPTION_TERMINAL_TYPE            = 24
OPTION_WINDOW_SIZE              = 31
OPTION_TERMINAL_SPEED           = 32
OPTION_REMOTE_FLOW_CONTROL      = 33
OPTION_LINEMODE                 = 34
OPTION_ENVIRONMENT_VARIABLES    = 36

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

        self.inIAC = False
        self.iacIndex = None
        self.iacBits = []

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

    def OnBytesReceived(self, s):
        # As soon as the incoming text is received, process it.
        i = 0
        while i < len(s):
            if self.inIAC:
                self.iacBits.append(s[i])
            elif s[i] == IAC:
                self.inIAC = True
            i += 1
        Connection.OnBytesReceived(self, s)

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

            if self.echo:
                if s == '\x08':
                    self.send(s+" ")
                self.send(s)
            buf += s

    # -----------------------------------------------------------------------
    # handle_read_event - Callback from asyncore.poll()
    # -----------------------------------------------------------------------
    # We override this to get around the superfluous automatic connection logic.
    # -----------------------------------------------------------------------
    def handle_read_event(self):
        Connection.handle_read(self)

    # -----------------------------------------------------------------------
    # handle_write_event - Callback from asyncore.poll()
    # -----------------------------------------------------------------------
    # We override this to get around the superfluous automatic connection logic.
    # -----------------------------------------------------------------------
    def handle_write_event(self):
        self.do_send()
