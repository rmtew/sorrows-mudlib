import stackless
from stacklesslib.main import sleep as tasklet_sleep
from mudlib.services.net import Connection
from mudlib import User

class TelnetConnection(Connection):
    def Setup(self, service, connectionID, echo=False):
        Connection.Setup(self, service, connectionID)

        self.suppressEcho = False

        self.echo = echo
        self.consoleColumns = 80
        self.consoleRows = 24
        self.terminalType = None
        self.terminalTypes = []

        self.optionEcho = False
        self.optionLineMode = True
        self.readlineBuffer = ""

        self.telneg = TelnetNegotiation(self.TelnetNegotiationSend, self.TelnetSubnegotiation, self.TelnetCommand)

        if False:
            self.user = None
            self.preLoginBuffer = StringIO.StringIO()
            stackless.tasklet(self._ManageConnectionPreLogin)()

        self.user = User(self, "login")
        self.user.SetupInputStack()
        
        stackless.tasklet(self.ManageConnection)()

    def SetPasswordMode(self, flag):
        if flag:
            self.suppressEcho = True
            # self.telneg.will_echo()
        else:
            self.suppressEcho = False
            # self.telneg.wont_echo()

    def TelnetNegotiationSend(self, data):
        self.service and self.service.LogDebug("SEND(%s)%s%s", self.user.name, self.clientAddress, [ord(c) for c in data])
        self.send(data)

    def TelnetCommand(self, command, option):
        # print "TELNET COMMAND", command, option
        if command == "DO":
            if option == "ECHO":
                self.echo = True

    def TelnetSubnegotiation(self, result):
        if result.command == NAWS:
            self.service.LogDebug("TERMINAL SIZE %s (%s)%s", result.parameters, self.user.name, self.clientAddress)
            self.consoleColumns, self.consoleRows = result.parameters

            self.user.inputstack.OnTerminalSizeChanged(*result.parameters)
        elif result.command == TTYPE:
            if self.terminalType and result.parameters == [ self.terminalType ]:
                self.service.LogDebug("TERMINAL TYPE %s (%s)%s", self.terminalType, self.user.name, self.clientAddress)
                return

            self.service.LogDebug("TERMINAL TYPES %s (%s)%s", result.parameters, self.user.name, self.clientAddress)
            self.terminalTypes = result.parameters

            # Select the first one the client offered.
            self.terminalType = result.parameters[0]
            self.telneg.do_ttype(self.terminalType)
        elif result.command == NEW_ENVIRON:
            self.service.LogDebug("ENVIRONMENT VARIABLES %s (%s)%s", result.parameters, self.user.name, self.clientAddress)
            for k, v in result.parameters:
                if k == "SYSTEMTYPE" and v == "WIN32":
                    self.telneg.will_echo()
                    break
        else:
            raise Exception("Unhandled subnegotiation", result)

    def ManageConnection(self):
        while not self.released:
            if not self._ManageConnection():
                break

    def _ManageConnection(self):
        if self.optionLineMode:
            input = self.readline()
        else:
            input = self.read(65536)
            # We may recieve an empty string if there was only negotiation.
            if input == "":
                return True

        if input is None:
            return False

        try:
            self.user.ReceiveInput(input)
        except Exception:
            self.service.LogException("Error dispatching input")
        return True

    def _ManageConnectionPreLogin(self):
        dataQueue = []

        def CollectIncomingData():
            data = ""
            while not self.released and data is not None:
                data = self.read(65536)
                dataQueue.append(data)

        workerTasklet = stackless.tasklet(CollectIncomingData)()

        self.send("\x1b[0c")
        self.send("MUD\r\n")

        slept = 0
        while not self.released:
            for data in dataQueue:
                if data is None:
                    return
                # print "RECEIVED AFTER", slept, "DATA", data
            del dataQueue[:]

            tasklet_sleep(0.01)
            slept += 0.01

    def OnDisconnection(self):
        super(TelnetConnection, self).OnDisconnection()
    
        # Notify the service of the disconnection.
        if self.user:
            self.user.OnTelnetDisconnection()
            self.user = None

        self.service.OnTelnetDisconnection(self)

    def read(self, bytes):
        s = self.recv(65536)
        # print "INPUT-CHARS", [ ord(c) for c in s ], s
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
        buf = self.readlineBuffer

        while True:
            # We need to handle all the different line endings which clients may send:
            #   \r  \r\n  \n
            ret = ""
            rIdx = buf.find('\r')
            if rIdx == -1:
                rIdx = buf.find('\n')
                if rIdx > -1:
                    ret = buf[:rIdx]
                    self.readlineBuffer = buf[rIdx+1:]
            else:
                ret = buf[:rIdx]
                if len(buf) > rIdx+1 and buf[rIdx+1] == '\n':
                    self.readlineBuffer = buf[rIdx+2:]
                else:
                    self.readlineBuffer = buf[rIdx+1:]

            if len(ret) or rIdx == 0:
                i = ret.find('\x08')
                while i > -1:
                    if i == 0:
                        ret = ret[1:]
                    else:
                        ret = ret[:i-1] + ret[i+1:]
                    i = ret.find('\x08')

                # print "INPUT-LINE", [ ord(c) for c in ret ], ret
                return ret

            s = self.recv(65536)
            if s == "":
                return None
            # print "INPUT-RECEIVED", [ ord(c) for c in s ]
            #if s[0] == "\x1b":
            #    print "ESCAPE-SEQUENCE-PENDING", s

            for s2 in self.telneg.feed(s):            
                # This is so not optimal yet, but it is correct which is good for now.
                for i, c in enumerate(s2):
                    if self.echo and not self.suppressEcho:
                        # print "ECHO", c
                        if c == '\x08':
                            self.send(c +" ")
                        elif c == '\r' and i == len(s2)-1:
                            # \r and \n are expected to come in pairs.
                            # If \r is the final character, no \n was sent.
                            self.send('\n')
                        self.send(c)
                    buf += c

# ---- TELNET NEGOTIATION ----
import StringIO, logging

logger = logging.getLogger("telopt")
logger.setLevel(logging.INFO)

negotiation_tokens = {
    chr(255):    "IAC",      # "Interpret As Command"

    chr(253):    "DO",
    chr(254):    "DONT",
    chr(251):    "WILL",
    chr(252):    "WONT",
    
    chr(240):    "SE",       # Subnegotiation End
    chr(241):    "NOP",      # No Operation
    chr(242):    "DM",       # Data Mark
    chr(243):    "BRK",      # Break
    chr(244):    "IP",       # Interrupt process
    chr(245):    "AO",       # Abort output
    chr(246):    "AYT",      # Are You There
    chr(247):    "EC",       # Erase Character
    chr(248):    "EL",       # Erase Line
    chr(249):    "GA",       # Go Ahead
    chr(250):    "SB",       # Subnegotiation Begin
}

for k, v in negotiation_tokens.iteritems():
    globals()[v] = k

negotiation_functions= set(i for i in range(240, 250))

IS          = chr(0)
SEND        = chr(1)
INFO        = chr(2)

VAR         = chr(0)
VALUE       = chr(1)
ESC         = chr(2)
USERVAR     = chr(3)

BINARY      = chr(0)        # 8-bit data path
ECHO        = chr(1)        # Echo
SGA         = chr(3)        # SGA
TTYPE       = chr(24)       # Terminal type
NAWS        = chr(31)       # Window size
TERMINAL_SPEED = chr(32)    # Terminal speed
LINEMODE    = chr(34)       # Linemode option
NEW_ENVIRON = chr(39)       # New environment variables

COMPRESS1   = chr(85)       # MCCP - Mud Client Compression Protocol, v1
COMPRESS2   = chr(86)       # MCCP - Mud Client Compression Protocol, v2
MCP         = chr(90)       # MSP  - Mud Sound Protocol
MXP         = chr(91)       # MXP  - Mud eXtension Protocol

negotiation_options = {
    ECHO:           "ECHO",
    SGA:            "SGA",
    TTYPE:          "TTYPE",
    NAWS:           "NAWS",
    TERMINAL_SPEED: "TERMINAL-SPEED",
    NEW_ENVIRON:    "NEW-ENVIRON",
}


class TelnetNegotiation:
    def __init__(self, send_cb, subnegotiation_cb=None, command_cb=None):
        self.send_cb = send_cb
        self.subnegotiation_cb = subnegotiation_cb
        self.command_cb = command_cb

        self.queue = []
    
        self.__sent = {}
        self.__received = {}

        self.preferred_terminal_type = None
        self.terminal_types = []

    def will_echo(self):
        #if self.__received.get(ECHO) == DO:
        #    return
        self._send(WILL, ECHO)
        # The specification says to behave as if it has been accepted.
        if self.command_cb:
            self.command_cb("DO", "ECHO")

    def wont_echo(self):
        self._send(WONT, ECHO)

    def do_linemode(self):
        self._send(DO, LINEMODE)

    def do_naws(self):
        self._send(DO, NAWS)

    def do_sga(self):
        self._send(DO, SGA)

    def will_sga(self):
        self._send(WILL, SGA)

    def do_new_environ(self):
        self._send(DO, NEW_ENVIRON)

    def do_mxp(self):
        self._send(DO, MCP)

    def do_ttype(self, preferred_terminal_type=None):
        self.preferred_terminal_type = preferred_terminal_type
        self._send(DO, TTYPE)

    def _send(self, command, option):
        logger.debug("SEND command %s (%d) %s (%d)", negotiation_tokens[command], ord(command), negotiation_options.get(option, "?"), ord(option))
        self.send_cb(IAC + command + option)
        self.__sent[option] = command

    def feed(self, data):        
        """
        Parses the supplied textual data, processing any embedded negotiation
        options that are present, and yielding the actual text that it
        encounters.
        """

        # If we are not in negotiation, we may be able to just hand back text.
        if not len(self.queue):
            leading_text, option, data = data.partition(IAC)
            if leading_text:
                yield leading_text
            if option == data == "":
                return
            self._negotiation(option)

        i = 0
        for j, char in enumerate(data):
            if self._negotiation(char):
                text = data[i:j]
                if text:
                    yield text
                i = j+1

        text = data[i:j+1]
        if text:
            yield text            

    def _negotiation(self, byte):
        if len(self.queue) == 0:
            if byte != IAC:             # Literal value.
                return False

            self.queue.append(byte)
        elif len(self.queue) == 1:
            if byte == IAC:             # Literal value of 255.
                self.queue = []
                return False

            elif byte in negotiation_functions:
                self._negotiation_function(byte)
                self.queue = []
                return True

            self.queue.append(byte)
        elif len(self.queue) == 2:
            command = self.queue[1]
            if command != SB:           # Negotiation command.
                self._negotiation_command(command, byte)
                self.queue = []
                return True

            self.queue.append(byte)
        else:
            if self.queue[-1] == IAC:
                if byte == IAC:
                    self.queue.pop()    # Literal value of 255.
                    return False

                elif byte == SE:        # End of subnegotiation.
                    self.queue.append(byte)
                    self._subnegotiation()
                    self.queue = []
                    return True

            self.queue.append(byte)

        return True

    def _negotiation_function(self, command):
        logger.debug("RECV function %s", ord(command))

    def _negotiation_command(self, command, option):
        logger.debug("RECV command %s (%d) %s (%d)", negotiation_tokens[command], ord(command), negotiation_options.get(option, "?"), ord(option))

        self.__received[option] = command

        if command == DO:
            pass
        elif command == DONT:
            pass
        elif command == WILL:
            if option == TTYPE:
                self._send_subnegotiation(TTYPE, SEND)
            elif option == NEW_ENVIRON:
                variables = (
                    # VAR, "USER",           # Crashes Windows Telnet.
                    VAR, "SYSTEMTYPE",
                    VAR, "ACCT",
                    VAR, "JOB",
                    VAR, "PRINTER",
                    VAR, "DISPLAY",
                )
                self._send_subnegotiation(NEW_ENVIRON, SEND, *variables)
            elif option == SGA:
                if self.__sent.get(option) is None:
                    self._send(DO, SGA)
        elif command == WONT:
            pass

        if self.command_cb:
            commandName = negotiation_tokens[command]
            optionName = negotiation_options.get(option, None)
            if optionName is not None:
                self.command_cb(commandName, optionName)

    def _send_subnegotiation(self, *args):
        self.send_cb(IAC+SB+ "".join(args) +IAC+SE)

    def _subnegotiation(self):
        logger.debug("subnegotiation %s", [ ord(c) for c in self.queue ])
        # [ IAC, SB, command, ..., IAC, SE ]
        
        result = None
        command = self.queue[2]

        if command == NAWS:
            result = self._subnegotiation_naws()
        elif command == TTYPE:
            result = self._subnegotiation_ttype()
        elif command == NEW_ENVIRON:
            result = self._subnegotiation_new_environ()
        else:
            logger.error("subnegotiation unprocessed")

        if result and self.subnegotiation_cb:
            self.subnegotiation_cb(result)

    def _subnegotiation_naws(self):
        width = (ord(self.queue[3]) << 8) + ord(self.queue[4])
        height = (ord(self.queue[5]) << 8) + ord(self.queue[6])

        result = Subnegotiation(NAWS)
        result.Add(width)
        result.Add(height)

        return result

    def _subnegotiation_ttype(self):
        result = None

        if self.queue[3] != IS: # Expected structure [ IAC SB TTYPE IS name IAC SE ].
            return result

        # Basically each one we are informed of is a selection.  So we
        # need to select each offered one to identify the range, and then
        # reselect until we have our preferred one selected.

        terminal_type = ("".join(self.queue[4:-2])).lower()
        if self.preferred_terminal_type is None:
            # Select terminal types until we have covered all the options.
            if terminal_type not in self.terminal_types:
                self.terminal_types.append(terminal_type)
                # Ask for the next terminal type.
                self._send_subnegotiation(TTYPE, SEND)
            else:
                # Application requested enumeration of terminal types.
                result = Subnegotiation(TTYPE)
                for value in self.terminal_types:
                    result.Add(value)

                self.terminal_types = []
        elif terminal_type == self.preferred_terminal_type:
            # The exact match equals success.
            result = Subnegotiation(TTYPE)
            result.Add(terminal_type)
        elif terminal_type in self.terminal_types:
            # No match equals failure.
            result = Subnegotiation(TTYPE)
        else:
            self.terminal_types.append(terminal_type)
            # Ask for the next terminal type.
            self._send_subnegotiation(TTYPE, SEND)

        return result

    def _subnegotiation_new_environ(self):
        result = None

        if self.queue[3] not in (IS, INFO):
            return result

        result = Subnegotiation(NEW_ENVIRON)

        variableName = None
        variableValue = None
        for i in range(4, len(self.queue)):
            c = self.queue[i]
            if c in (VAR, USERVAR, IAC):
                if variableName is not None:
                    if variableValue is None:
                        value = ""
                    else:
                        value = variableValue.getvalue()
                    if len(value):
                        result.Add((variableName.getvalue(), value))
                    variableName = None
                    variableValue = None
                    
            if c == IAC:
                break
            elif c == VAR or c == USERVAR:
                variableName = StringIO.StringIO()
            elif c == VALUE:
                variableValue = StringIO.StringIO()
            elif variableValue is not None:
                variableValue.write(c)
            elif variableName is not None:
                variableName.write(c)
            else:
                logger.error("Bad NEW-ENVIRON subnegotiation char %d", ord(c))
            
        return result


class Subnegotiation:
    def __init__(self, command):
        self.command = command
        self.parameters = []
        
    def Add(self, value):
        self.parameters.append(value)

