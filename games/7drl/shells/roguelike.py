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
        self.ShowCursor(False)
        self.DisplayScreen()

    # ------------------------------------------------------------------------

    def OnRemovalFromStack(self):
        msg = ""

        self.user.connection.optionLineMode = self.oldOptionLineMode
        self.user.connection.telneg.request_will_echo()
        self.user.Tell(EC_RESET_TERMINAL + EC_CLEAR_SCREEN + msg)

    def OnTerminalSizeChanged(self, rows, columns):
        self.DisplayScreen()

    def ReceiveInput(self, s):
        self._ReceiveInput(s)

    def _ReceiveInput(self, s):
        if s == chr(27): # Escape
            self.stack.Pop()
            self.user.ManualDisconnection()
            return

        if s == chr(18):
            self.lastStatusBar = " Screen refreshed"
            self.DisplayScreen()
            return
        elif s == "\x1b[A": # Up cursor key.
            if self.playerY > self.titleOffset + 1:
                self.oldPlayerX = self.playerX
                self.oldPlayerY = self.playerY
                self.playerY -= 1
                self.UpdateView()
        elif s == "\x1b[B": # Down cursor key.
            if self.playerY < self.statusOffset - 1:
                self.oldPlayerX = self.playerX
                self.oldPlayerY = self.playerY
                self.playerY += 1
                self.UpdateView()
        elif s == "\x1b[C": # Right cursor key.
            if self.playerX < self.user.connection.consoleColumns:        
                self.oldPlayerX = self.playerX
                self.oldPlayerY = self.playerY
                self.playerX += 1
                self.UpdateView()
        elif s == "\x1b[D": # Left cursor key.
            if self.playerX > 1:        
                self.oldPlayerX = self.playerX
                self.oldPlayerY = self.playerY
                self.playerX -= 1
                self.UpdateView()

        # Fallthrough.
        t = str([ ord(c) for c in s ])
        s = s.replace('\x1b', 'ESC')
        s = "".join(c for c in s if ord(c) >= 32)
        self.UpdateStatusBar(" Input: \"%s\" %s" % (s, t))

    # Display ----------------------------------------------------------------

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

        self.UpdateView()

        self.UpdateTitle()
        self.UpdateStatusBar(self.lastStatusBar)

    def UpdateView(self):
        playerX = getattr(self, "playerX", None)
        if playerX is None:
            windowLength = self.windowEndOffset - self.windowOffset + 1
            playerX = self.playerX = self.user.connection.consoleColumns / 2
            playerY = self.playerY = self.windowOffset + windowLength/2
            oldPlayerX = self.oldPlayerX = playerX
            oldPlayerY = self.oldPlayerY = playerY
        else:
            playerY = self.playerY
            oldPlayerX = self.oldPlayerX
            oldPlayerY = self.oldPlayerY

        if oldPlayerX != playerX or oldPlayerY != playerY:
            self.MoveCursor(oldPlayerX, oldPlayerY)
            self.EraseCharacters(1)

        self.MoveCursor(playerX, playerY)
        self.user.Write("@")

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

    # ANSI Cursor ------------------------------------------------------------

    def ShowCursor(self, flag=True):
        if flag:
            s = "\x1b[?25h"
        else:
            s = "\x1b[?25l"
        self.user.Write(s)

    def MoveCursor(self, x, y, clear=False):
        s = "\x1b[%d;%dH" % (y, x)
        if clear:
            s += EC_CLEAR_LINE
        self.user.Write(s)

    def SaveCursorPosition(self):
        self.user.Write("\x1b[s")
        
    def RestoreCursorPosition(self):
        self.user.Write("\x1b[u")

    # ANSI Scrolling ---------------------------------------------------------

    def SetScrollingRows(self, yLow, yHigh):
        self.user.Write("\x1b[%d;%dr" % (yLow, yHigh))

    def ScrollWindowUp(self):
        self.MoveCursor(self.windowOffset + 2)
        self.user.Write(EC_SCROLL_UP)

    def ScrollWindowDown(self):
        self.MoveCursor(self.windowOffset)
        self.user.Write(EC_SCROLL_DOWN)

    # ANSI Attribute ---------------------------------------------------------

    def RepeatLastCharacter(self, times=1):
        self.user.Write("\x1b[%db" % times)

    def EraseCharacters(self, times=1):
        self.user.Write("\x1b[%dX" % times)