import uthread
from mudlib import Shell, InputHandler

ROWS = 25

EC_CLEAR_LINE        = "\x1b[2K"
EC_CLEAR_SCREEN      = "\x1b[2J"
EC_HOME_CURSOR       = "\x1b[1;1H"
EC_RESET_TERMINAL    = "\x1bc"
EC_REVERSE_VIDEO_ON  = "\x1b[7m"
EC_REVERSE_VIDEO_OFF = "\x1b[27m"
EC_SCROLL_UP         = "\x1bM"
EC_SCROLL_DOWN       = "\x1bD"


class RoguelikeShell(Shell):
    def Setup(self, stack):
        Shell.Setup(self, stack)

        handler = InputHandler()
        handler.Setup(self, self.ReceiveInput, None, 0)
        stack.Push(handler)

        self.oldOptionLineMode = self.user.connection.optionLineMode
        self.user.connection.optionLineMode = False

        self.windowOffset = 0
        self.windowLength = 0
        self.titleOffset = 0
        self.statusOffset = 0

        self.status = "-"
        self.lastStatusBar = "-"

        self.user.connection.telneg.password_mode_on()
        self.DisplayScreen()

    def OnTerminalSizeChanged(self, rows, columns):
        self.DisplayScreen()

    def ReceiveInput(self, s):
        for c in s:
            self._ReceiveInput(c)

    def _ReceiveInput(self, c):
        if c == chr(27):
            self.stack.Pop()
            self.user.ManualDisconnection()
            return

        # Fallthrough.
        s = "= %d" % ord(c)
        self.UpdateStatusBar(" Unknown command \"%s\" %s" % (c, s))

    # ------------------------------------------------------------------------

    def UpdateTitle(self):
        pre = EC_HOME_CURSOR
        
        left = "  "+ sorrows.data.config.identity.name
        right = self.status +"  "

        self.user.Write(pre)
        self.user.Write(EC_REVERSE_VIDEO_ON + left + (" " * (self.user.connection.consoleColumns - len(left) - len(right))) + right + EC_REVERSE_VIDEO_OFF)

    def UpdateStatusBar(self, s):
        self.lastStatusBar = s

        self.MoveCursor(0, self.statusOffset, clear=True)
        self.user.Write(EC_REVERSE_VIDEO_ON + s + (" " * (self.user.connection.consoleColumns - len(s))) + EC_REVERSE_VIDEO_OFF)
        self.MoveCursor(0, self.statusOffset, clear=False)

    def MoveCursor(self, x, y, clear=False):
        s = "\x1b[%d;%dH" % (y, x)
        if clear:
            s += EC_CLEAR_LINE
        self.user.Write(s)

    def SetScrollingRows(self, yLow, yHigh):
        self.user.Write("\x1b[%d;%dr" % (yLow, yHigh))

    def ScrollWindowUp(self):
        self.MoveCursor(self.windowOffset + 2)
        self.user.Write(EC_SCROLL_UP)

    def ScrollWindowDown(self):
        self.MoveCursor(self.windowOffset)
        self.user.Write(EC_SCROLL_DOWN)

    def DisplayScreen(self):
        self.user.Write(EC_CLEAR_SCREEN)

        # The layout of the screen is:
        # - Title bar.
        # - Window.
        # - Status bar.

        rows = self.user.connection.consoleRows

        self.titleOffset = 1
        self.statusOffset = rows
        self.windowOffset = self.titleOffset + 1
        self.windowEndOffset = rows - 1

        self.SetScrollingRows(self.windowOffset, self.windowEndOffset)
        # ----
        windowLength = self.windowEndOffset - self.windowOffset + 1
        for i in range(0, windowLength):
            self.MoveCursor(0, self.windowOffset + i)
            self.user.Write("%d" % i)
        self.MoveCursor(0, self.statusOffset)

        self.UpdateTitle()
        self.UpdateStatusBar(self.lastStatusBar)

    def OnRemovalFromStack(self):
        msg = "Simulation exited."

        self.user.connection.optionLineMode = self.oldOptionLineMode
        self.user.connection.telneg.request_will_echo()
        self.user.Tell(EC_RESET_TERMINAL + EC_CLEAR_SCREEN + msg)
