import string
from mudlib import Shell, InputHandler

# Standard telnet window size.
COLS = 80
ROWS = 25

EC_CLEAR_LINE        = "\x1b[2K"
EC_CLEAR_SCREEN      = "\x1b[2J"
EC_HOME_CURSOR       = "\x1b[1;1H"
EC_RESET_TERMINAL    = "\x1bc"
EC_REVERSE_VIDEO_ON  = "\x1b[7m"
EC_REVERSE_VIDEO_OFF = "\x1b[27m"
EC_SCROLL_UP         = "\x1bM"
EC_SCROLL_DOWN       = "\x1bD"


class SimulationShell(Shell):
    def Setup(self, stack):
        Shell.Setup(self, stack)

        handler = InputHandler()
        handler.Setup(self, self.ReceiveInput, self.WritePrompt, 0)
        stack.Push(handler)

        self.windowOffset = 0
        self.windowLength = 0
        self.statusOffset = 0
        self.status = "-"
        self.name = "simulation"

        self.DisplayScreen()

    def ReceiveInput(self, s):
        command = s.strip()
        # Ignore sent carriage returns.
        if len(command) == 0:
            return
        if command in ("exit", "quit"):
            self.stack.Pop()
            return

        if command == "xxx":
            pass
        else:
            s = "["
            for i in range(len(command)):
                s += " %d" % ord(command[i])
            s += " ]"
            self.UpdateResult("Unknown command \"%s\" %d %s." % (command, len(command), s))

    def WritePrompt(self):
        return '] '

    # ------------------------------------------------------------------------

    def UpdateTitle(self):
        pre = EC_HOME_CURSOR
        
        left = "  "+ self.name
        right = self.status +"  "

        self.user.Write(pre)
        self.user.Write(EC_REVERSE_VIDEO_ON + left + (" " * (COLS - len(left) - len(right))) + right + EC_REVERSE_VIDEO_OFF)

    def UpdateResult(self, s):
        self.MoveCursor(0, self.windowLength + self.windowOffset + 1, clear=True)
        self.user.Write(s)
        self.MoveCursor(0, self.windowLength + self.windowOffset, clear=True)

    def MoveCursor(self, x, y, clear=False):
        s = "\x1b[%d;%dH" % (y, x)
        if clear:
            s += EC_CLEAR_LINE
        self.user.Write(s)

    def SetScrollingRows(self, yLow, yHigh):
        self.user.Write("\x1b[%d;%dr" % (yLow, yHigh))

    def ScrollWindowUp(self):
        self.MoveCursor(self.windowOffset + self.windowLength)
        self.user.Write(EC_SCROLL_UP)

    def ScrollWindowDown(self):
        self.MoveCursor(self.windowOffset)
        self.user.Write(EC_SCROLL_DOWN)

    def DisplayScreen(self):
        self.user.connection.telneg.request_wont_echo()
        self.user.Write(EC_CLEAR_SCREEN)
        self.UpdateTitle()

        # The layout of the screen is:
        # - Title bar.
        # - 2 blank lines.
        # - Window.
        # - 2 blank lines.
        # - Status bar.

        self.statusOffset = ROWS
        self.windowOffset = 1 + 3
        self.windowLength = self.statusOffset - self.windowOffset - 3

        self.SetScrollingRows(self.windowOffset, self.windowLength)
        # ----
        self.MoveCursor(0, self.windowOffset)
        for i in range(0, 30):
            self.user.Tell("%d" % i)
        # ----
        self.MoveCursor(0, self.windowLength + self.windowOffset)

    def OnRemovalFromStack(self):
        msg = "Simulation exited."
        self.user.connection.telneg.request_will_echo()
        self.user.Tell(EC_RESET_TERMINAL + EC_CLEAR_SCREEN + msg)
