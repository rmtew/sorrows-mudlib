import random, array, math, StringIO, time
import uthread, fov
from mudlib import Shell, InputHandler

# TODO LIST -------------------------------------------------------------------

# FEATURE:  Input filter for keyboard mode.  Make laptop key mapping work.
# REFACTOR: Move the movement view update code out of the input handler.
# REFACTOR: Revise the movement view update code to be understandable.

# ASCII CODES -----------------------------------------------------------------

# Escape codes.

ESC_CLEAR_LINE        = "\x1b[2K"
ESC_CLEAR_SCREEN      = "\x1b[2J"
ESC_HOME_CURSOR       = "\x1b[1;1H"
ESC_RESET_TERMINAL    = "\x1bc"
ESC_REVERSE_VIDEO_ON  = "\x1b[7m"
ESC_REVERSE_VIDEO_OFF = "\x1b[27m"
ESC_CURSOR_DOWN       = "\x1b[B"
ESC_SCROLL_UP         = "\x1bM"
ESC_SCROLL_DOWN       = "\x1bD"
ESC_ERASE_LINE        = "\x1b[K"
ESC_ERASE_DOWN        = "\x1b[J"    # WARNING: Does not respect scrolling regions.
ESC_ERASE_UP          = "\x1b[1J"   # WARNING: Does not respect scrolling regions.
ESC_GFX_BLUE_FG       = "\x1b[34m"
ESC_GFX_OFF           = "\x1b[0m"

# Control codes.

CTRL_E                = chr(5)  # ENQ

# MAP -------------------------------------------------------------------------

# D - Door
# @ - Player starting location
# X - Solid rock

levelMap = """
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXX                      D XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXX X XXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXDXDXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXX D    XXXXXXXXXX             XXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXX    X                      XXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXX D    X XXXXXXXX             XXXXXXXXXXXXXXXX XXXXX     X     XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXX    D XXXXXXXX             XXXXXXXXXXXXXXXX XXXXX     X     XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
X     D    X XXXXXXXX             XXXXXXXXXXXXXXXX XXXXX     X     XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXX    X                      XXXXXXXXXXXXXX     XXXXXDXXXXXDXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXX D    XXXXXXXXXX             XXXXXXXX           D              D XXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXDXDXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXX     XXXXXDXXXXXDXXXX XXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXX X XXXXXXXXXXXXXXXXXXXXXXXXXXXXX     XXXXX XXXXX     X     X  X   XXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  @  XXXXX XXXXX     X     X XX   XXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     XXXXX XXXXX     X     X X    XXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXX XXXXDXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXX                           X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX X
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
"""

CHAR_TILE = "@"
WALL_TILE = "X"
FLOOR_TILE = " "
DOOR_TILE = "D"

displayTiles = {
    CHAR_TILE: chr(250),
    WALL_TILE: chr(219),
    FLOOR_TILE: chr(250),
    DOOR_TILE: "D",
}

TILE_VISIBLE = 1
TILE_OPEN = 2

VIEW_RADIUS = 4

MODE_GAMEPLAY               = 1

MODE_FIRST_MENU             = 10
MODE_ESCAPE_MENU            = 10
MODE_DEBUG_MENU             = 11
MODE_KEYBOARD_MENU          = 12
MODE_TELNETCLIENT_MENU      = 13
MODE_LAST_MENU              = 13

MODE_FIRST_DISPLAY          = 20
MODE_DEBUG_DISPLAY          = 20
MODE_LAST_DISPLAY           = 20

MODE_NAMES = {
    MODE_ESCAPE_MENU:           "Menu",
    MODE_DEBUG_MENU:            "Debug Menu",
    MODE_KEYBOARD_MENU:         "Keyboard Menu",
    MODE_TELNETCLIENT_MENU:     "Telnet Client Menu",
}


class RoguelikeShell(Shell):
    def Setup(self, stack):
        Shell.Setup(self, stack)

        handler = InputHandler()
        handler.Setup(self, self.ReceiveInput, None, 0)
        stack.Push(handler)

        self.oldOptionLineMode = self.user.connection.optionLineMode
        self.user.connection.optionLineMode = False

        # Defaults..
        self.keyboard = "computer"
        self.menuOptions = []
        self.menuSelection = 0

        self.status = "-"
        self.lastStatusBar = "-"

        # Send client-side information.
        self.user.connection.telneg.password_mode_on()
        self.ShowCursor(False)
        self.QueryClientName()

        # Process the map.
        self.mapRows = [
            line.strip()
            for line in levelMap.split("\n")
            if len(line) and line[0] == 'X'
        ]
        for i, line in enumerate(self.mapRows):
            x = line.find("@")
            if x != -1:
               self.playerStartX = x
               self.playerStartY = i
               break
        else:
            raise Exception("Map did not provide a player starting position")

        self.mapWidth = len(self.mapRows[0])
        self.mapHeight = len(self.mapRows)
        self.mapArray = array.array('B', (0 for i in xrange(self.mapHeight * self.mapWidth)))

        self.playerX = self.playerStartX
        self.playerY = self.playerStartY

        rows = self.user.connection.consoleRows
        cols = self.user.connection.consoleColumns
        self.OnTerminalSizeChanged(rows, cols, redraw=False)
        self.RecalculateWorldView()

        self.charsetResetSequence = None

        self.UpdateTitle()
        self.UpdateStatusBar("")
        self.EnterKeyboardMenu()

    def QueryClientName(self):
        self.clientName = None
        self.user.Write(CTRL_E)

    def SetClientName(self, clientName):
        self.clientName = clientName.lower()

        if self.clientName == "putty":
            self.charsetResetSequence = "\x1b(U"
            self.ResetCharset()

    def SetMode(self, mode, status=None):
        if status is None:
            status = MODE_NAMES.get(mode, None)
        if status is not None:
            self.UpdateTitle(status)
        self.mode = mode

    # Events ------------------------------------------------------------------

    def OnRemovalFromStack(self):
        self.user.connection.optionLineMode = self.oldOptionLineMode
        self.user.connection.telneg.request_will_echo()
        self.user.Write(ESC_RESET_TERMINAL)
        self.ScrollWindowUp()
        self.MoveCursor(0, self.statusOffset)

    def OnTerminalSizeChanged(self, rows, columns, redraw=True):
        # Window partitioning offsets and sizes.
        self.titleOffset = 1
        self.statusOffset = rows

        self.windowXStartOffset = 1
        self.windowXEndOffset = columns - 1
        self.windowYStartOffset = self.titleOffset + 1
        self.windowYEndOffset = rows - 1

        self.windowWidth = columns
        self.windowHeight = rows - 2

        self.RecalculateWorldView()

        self.SetScrollingRows(self.windowYStartOffset, self.windowYEndOffset)

        if redraw:
            self.DisplayScreen()

    def ReceiveInput(self, s):
        if self.mode == MODE_GAMEPLAY:
            self.ReceiveInput_Gameplay(s)
        elif MODE_FIRST_MENU <= self.mode <= MODE_LAST_MENU:
            if self.mode == MODE_KEYBOARD_MENU:
                # We've sent <ENQ>, check for Putty's response. 
                if s == "PuTTY":
                    self.SetClientName(s)
                    # Refresh the menu with proper characters.
                    self.DisplayMenu(self.mode, self.menuOptions, selected=self.menuSelection)

            self.ReceiveInput_Menu(s)
        elif MODE_FIRST_DISPLAY <= self.mode <= MODE_LAST_DISPLAY:
            self.ReceiveInput_DisplayPage(s)

    # Input -------------------------------------------------------------------

    def ReceiveInput_DisplayPage(self, s):
        # Any keypress returns to the previous mode.
        self.MenuActionBack()

    def ReceiveInput_Menu(self, s):
        movementShift = {
            "\x1b[A": -1,
            "\x1b[B":  1,
        }

        def MenuAction(label):
            f = getattr(self, "MenuAction"+ label, None)
            if f is not None:
                f()

        if s == chr(27): # Escape
            return self.MenuActionBack()
        elif s == chr(18): # CTRL-r
            return self.DisplayMenu(self.mode, self.menuOptions, selected=self.menuSelection)
        elif s in movementShift:
            shift = movementShift[s]
            lastOffset = len(self.menuOptions) - 1
            if shift == -1 and self.menuSelection == 0:
                self.menuSelection = lastOffset
            elif shift == 1 and self.menuSelection == lastOffset:
                self.menuSelection = 0
            else:
                self.menuSelection += shift

            return self.DisplayMenu(self.mode, self.menuOptions, selected=self.menuSelection, redraw=False)
        elif s == "\r\n":
            option = self.menuOptions[self.menuSelection]
            return MenuAction(option[1])
        else:
            # Otherwise, the action is specified by the menu.
            for t in self.menuOptions:
                hotkey = t[0].lower()
                if hotkey == s:
                    return MenuAction(t[1])

        # Fallthrough.
        t = str([ ord(c) for c in s ])
        s = s.replace('\x1b', 'ESC')
        s = "".join(c for c in s if ord(c) >= 32)
        self.UpdateStatusBar(" Input: \"%s\" %s" % (s, t))

    def ReceiveInput_Gameplay(self, s):
        if s == chr(27): # Escape
            self.EnterEscapeMenu()
            return

        if s == chr(5):
            windowUpperDistance = self.playerY - self.worldViewY
            worldViewLowerY = self.worldViewY + self.windowHeight
            windowLowerDistance = worldViewLowerY - self.playerY

            sio = StringIO.StringIO()
            self.SaveCursorPosition(sio=sio)
            args = self.playerX, self.playerY, self.worldViewX, self.worldViewY, worldViewLowerY
            self.UpdateStatusBar(" [%03d %03d] [%03d %03d-%03d]" % args, sio=sio)
            self.RestoreCursorPosition(sio=sio)
            self.user.Write(sio.getvalue())
            return
        elif s == chr(18):
            self.lastStatusBar = " Screen refreshed"
            self.DisplayScreen()
            return

        movementShift = {
            "\x1b[A": ( 0,-1),
            "\x1b[B": ( 0, 1),
            "\x1b[C": ( 1, 0),
            "\x1b[D": (-1, 0),
        }.get(s, None)
            
        if movementShift is not None:            
            newX = self.playerX + movementShift[0]
            newY = self.playerY + movementShift[1]

            # For now, can only move into empty spaces.
            tile = self.mapRows[newY][newX]
            flags = self.mapArray[self.mapWidth * newY + newX]
            passableTile = tile in (" ", "@")
            passableTile = passableTile or tile == "D" and (True or flags & TILE_OPEN)
            if passableTile:
                self.GameActionMove(newX, newY)
            return

        # Fallthrough.
        t = str([ ord(c) for c in s ])
        s = s.replace('\x1b', 'ESC')
        s = "".join(c for c in s if ord(c) >= 32)
        self.UpdateStatusBar(" Input: \"%s\" %s" % (s, t))

    # View --------------------------------------------------------------------

    def RecalculateWorldView(self):
        halfWidth = self.user.connection.consoleColumns / 2
        halfHeight = self.windowHeight / 2

        # World view offsets and sizes.
        self.worldViewX = self.playerX - halfWidth
        self.worldViewY = self.playerY - halfHeight

    # Display ----------------------------------------------------------------

    def DisplayScreen(self):
        self.user.Write(ESC_CLEAR_SCREEN)

        self.UpdateView()

        self.UpdateTitle()
        self.UpdateStatusBar(self.lastStatusBar)

    def UpdateView(self, sio=None):
        self.drawRanges = {}

        def fVisited(x, y):
            self.mapArray[y * self.mapWidth + x] |= TILE_VISIBLE

            if x < self.worldViewX or x > self.worldViewX + self.windowWidth:
                return
            if y < self.worldViewY or y > self.worldViewY + self.windowHeight+1:
                return
            
            if y in self.drawRanges:
                minX, maxX = self.drawRanges[y]
                self.drawRanges[y] = [ min(x, minX), max(x, maxX) ]
            else:
                self.drawRanges[y] = [ x, x ]

        def fBlocked(x, y):
            tile = self.mapRows[y][x]
            return tile not in (CHAR_TILE, " ")

        fov.fieldOfView(self.playerX, self.playerY, self.mapWidth, self.mapHeight, VIEW_RADIUS, fVisited, fBlocked)

        if sio is None:
            sio_ = StringIO.StringIO()
        else:
            sio_ = sio

        for y, (minX, maxX) in self.drawRanges.iteritems():            
            vMinX = (minX - self.worldViewX) + 1
            vMaxX = (maxX - self.worldViewX) + 1
            if vMinX < 1 or vMaxX > self.windowWidth:
                continue

            vy = (y - self.worldViewY) + 1
            if vy < self.windowYStartOffset or vy > self.windowYEndOffset:
                continue

            self.MoveCursor(vMinX, vy, sio=sio_)
            arr = array.array('c', (self.ViewedTile(x, y) for x in range(minX, maxX+1)))
            sio_.write(arr.tostring())

        self.UpdatePlayer(sio=sio_)

        if sio is None:
            self.user.Write(sio_.getvalue())

    def UpdateLineByWorldPosition(self, y, cnt=1, sio=None):
        # Find the map line.
        # Find the start and end of the map line parts to examine.
        # Find the first visible and last visible characters in the given line.
        # Clear the line.
        # Display the display tiles for that character range.

        screenY = (y - self.worldViewY) + self.windowYStartOffset
        for i in xrange(cnt):
            yi = (y + 1) + i

            if yi < 0 or yi >= self.mapHeight:
                #self.MoveCursor(self.windowXStartOffset + self.windowWidth/2 - 1, screenY + i, sio=sio)
                #sio.write("&&&")                
                continue

            xStart = self.worldViewX
            # Do not go outside the LHS bounds of the map.
            if xStart < 0:
                xStart = 0

            xEnd = xStart + self.windowWidth - 1
            # Do not go outside the RHS bounds of the map.
            if xEnd >= self.mapWidth:
                xEnd = self.mapWidth - 1

            rowOffset = yi * self.mapWidth
            for x in range(xStart, xEnd + 1):
                flags = self.mapArray[rowOffset + x]
                if flags & TILE_VISIBLE:
                    xStart = x
                    break

            for x in range(xEnd, xStart - 1, -1):
                flags = self.mapArray[rowOffset + x]
                if flags & TILE_VISIBLE:
                    xEnd = x
                    break
            else:
                #self.MoveCursor(self.windowXStartOffset + self.windowWidth/2 - 1, screenY + i, sio=sio)
                #sio.write("$$$")                
                continue

            screenX = (xStart - self.worldViewX) + self.windowXStartOffset
            self.MoveCursor(screenX, screenY + i, sio=sio)

            arr = array.array('c', (self.ViewedTile(x, yi, flag=True) for x in xrange(xStart, xEnd + 1)))
            if sio is None:
                self.user.Write(arr.tostring())
            else:
                sio.write(arr.tostring())

    def UpdateViewByWorldPosition(self, x, y, c, sio=None):
        vx = (x - self.worldViewX) + 1
        vy = (y - self.worldViewY) + 1
        self.MoveCursor(vx, vy, sio=sio)
        if sio is None:
            self.user.Write(c)
        else:
            sio.write(c)

    def UpdatePlayer(self, sio=None):
        self.UpdateViewByWorldPosition(self.playerX, self.playerY, "@", sio=sio)

    def UpdateTitle(self, newStatus=None):
        pre = ESC_HOME_CURSOR

        if newStatus is not None:
            self.status = newStatus
        
        left = "  "+ sorrows.data.config.identity.name
        right = self.status +"  "

        self.user.Write(pre)
        self.user.Write(ESC_REVERSE_VIDEO_ON + left + (" " * (self.user.connection.consoleColumns - len(left) - len(right))) + right + ESC_REVERSE_VIDEO_OFF)

    def UpdateStatusBar(self, s, sio=None):
        self.lastStatusBar = s

        self.MoveCursor(0, self.statusOffset, clear=True, sio=sio)
        s = ESC_REVERSE_VIDEO_ON + s + (" " * (self.user.connection.consoleColumns - len(s))) + ESC_REVERSE_VIDEO_OFF
        if sio is None:
            self.user.Write(s)
        else:
            sio.write(s)
        self.MoveCursor(0, self.statusOffset, clear=False, sio=sio)

    # Map Support ------------------------------------------------------------

    def ViewedTile(self, x, y, flag=False):
        flags = self.mapArray[y * self.mapWidth + x]
        if flags & TILE_VISIBLE:
            return self.GetDisplayTile(x, y)
        return " "

    def GetTile(self, x, y):
        return self.mapRows[y][x]

    def TranslateTileForDisplay(self, tile):
        dtile = displayTiles.get(tile, None)
        if dtile is not None:
            return dtile
        return tile
        
    def GetDisplayTile(self, x, y):
        if y < 0 or y >= len(self.mapRows):
            print "TILE ERROR/y", x, y
            return "?"
        if x < 0 or x >= len(self.mapRows[y]):
            print "TILE ERROR/x", x, y
            return "?"
        tile = self.mapRows[y][x]
        return self.TranslateTileForDisplay(tile)

    # ANSI Cursor ------------------------------------------------------------

    def ShowCursor(self, flag=True):
        if flag:
            s = "\x1b[?25h"
        else:
            s = "\x1b[?25l"
        self.user.Write(s)

    def MoveCursor(self, x, y, clear=False, sio=None):
        s = "\x1b[%d;%dH" % (y, x)
        if clear:
            s += ESC_CLEAR_LINE
        if sio is None:
            self.user.Write(s)
        else:
            sio.write(s)

    def SaveCursorPosition(self, sio=None):
        s = "\x1b[s"
        if sio is None:
            self.user.Write(s)
        else:
            sio.write(s)
        
    def RestoreCursorPosition(self, sio=None):
        s = "\x1b[u"
        if sio is None:
            self.user.Write(s)
        else:
            sio.write(s)

    # ANSI Scrolling ---------------------------------------------------------

    def SetScrollingRows(self, yLow, yHigh):
        self.user.Write("\x1b[%d;%dr" % (yLow, yHigh))

    def ResetScrollingRows(self):
        self.user.Write("\x1b[r")

    def ScrollWindowLeft(self, margin, sio=None):
        for i in xrange(self.windowHeight):
            self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset + i, sio=sio)
            self.DeleteCharacters(margin, sio=sio)

    def ScrollWindowRight(self, margin, sio=None):
        for i in xrange(self.windowHeight):
            self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset + i, sio=sio)
            self.InsertCharacters(margin, sio=sio)

    def ScrollWindowUp(self, cnt=1, sio=None):
        self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset, sio=sio)
        s = ESC_SCROLL_UP * cnt
        if sio is None:
            self.user.Write(s)
        else:
            sio.write(s)

    def ScrollWindowDown(self, cnt=1, sio=None):
        self.MoveCursor(self.windowXStartOffset, self.windowYEndOffset, sio=sio)
        s = ESC_SCROLL_DOWN * cnt
        if sio is None:
            self.user.Write(s)
        else:
            sio.write(s)

    def InsertCharacters(self, times=1, sio=None):
        s = "\x1b[%d@" % times
        if sio is None:
            self.user.Write(s)
        else:
            sio.write(s)

    def DeleteCharacters(self, times=1, sio=None):
        s = "\x1b[%dP" % times
        if sio is None:
            self.user.Write(s)
        else:
            sio.write(s)

    # ANSI Attribute ---------------------------------------------------------

    def RepeatLastCharacter(self, times=1):
        self.user.Write("\x1b[%db" % times)

    def EraseCharacters(self, times=1):
        self.user.Write("\x1b[%dX" % times)

    def ResetCharset(self, sio=None):
        if self.charsetResetSequence:
            if sio is None:
                self.user.Write(self.charsetResetSequence)
            else:
                sio.write(self.charsetResetSequence)

    # Gameplay Support --------------------------------------------------------

    def GameActionMove(self, x, y):
        sio = StringIO.StringIO()

        if False: # Obsoleted by FoV.
            # Restore the tile under the player's old position.
            tile = self.GetDisplayTile(self.playerX, self.playerY)
            self.UpdateViewByWorldPosition(self.playerX, self.playerY, tile, sio=sio)

        self.playerX = x
        self.playerY = y

        windowLeftDistance = self.playerX - self.worldViewX
        halfWidth = self.windowWidth / 2

        if windowLeftDistance < VIEW_RADIUS:
            xShift = halfWidth - windowLeftDistance + 1
            self.worldViewX -= xShift
            self.ScrollWindowRight(xShift, sio=sio)
        else:
            windowRightDistance = (self.worldViewX + self.windowWidth) - self.playerX
            
            if windowRightDistance <= VIEW_RADIUS:
                xShift = halfWidth - windowRightDistance - 1
                self.worldViewX += xShift
                self.ScrollWindowLeft(xShift, sio=sio)

        windowUpperDistance = self.playerY - self.worldViewY
        halfHeight = self.windowHeight / 2

        # Has the player moved so their view falls outside the screen?
        # The player's line is counted in this calculation.
        if windowUpperDistance <= VIEW_RADIUS:
            # Distance needed to shift the player to the window center.
            # +1 to put them further from the side they are moving towards.
            yShift = halfHeight - windowUpperDistance + 1
            self.worldViewY -= yShift
            self.ScrollWindowUp(yShift, sio=sio)

            # Account for the remaining viewed distance (less the line the player is on).
            blankLines = (self.playerY - self.worldViewY) - 1
            self.UpdateLineByWorldPosition(self.worldViewY, cnt=blankLines, sio=sio)
        else:
            windowLowerDistance = (self.worldViewY + self.windowHeight) - self.playerY

            # Has the player moved so their view falls outside the screen?
            # The player's line is not counted in this calculation.
            if windowLowerDistance < VIEW_RADIUS:
                # Distance needed to shift the player to the window center.
                # -1 to put them further from the side they are moving towards.
                yShift = halfHeight - windowLowerDistance - 1
                self.worldViewY += yShift
                self.ScrollWindowDown(yShift, sio=sio)

                # Account for the view range and the line the player is on.
                blankLines = yShift + VIEW_RADIUS - 1
                self.UpdateLineByWorldPosition(self.playerY, cnt=blankLines, sio=sio)

        # Add an FoV update over the scrolled and filled in output.
        self.UpdateView(sio=sio)

        # Write the collected output to the player.
        self.user.Write(sio.getvalue())

    # Menu / Paging Support ---------------------------------------------------

    def DisplayMenu(self, mode, options, selected=0, redraw=True):
        # options = [
        #     (hotkey, label, description)
        # ]
        self.SetMode(mode)
        self.menuOptions = options
        self.menuSelection = selected

        screenWidth = self.user.connection.consoleColumns
    
        maxLabelSize = 0
        maxDescSize = 0
        for t in options:
            maxLabelSize = max(maxLabelSize, len(t[1]))
            maxDescSize = max(maxDescSize, len(t[2]))

        menuHeight = 2 + len(options) + len(options) - 1 + 2
        optionWidth = 2 + 1 + 3 + maxLabelSize + 2 + 1 + 1 + maxDescSize + 2
        screenXStart = (screenWidth - optionWidth) / 2
        screenYStart = self.windowYStartOffset + ((self.windowHeight / 2) - menuHeight / 2)

        screenY = screenYStart

        sio = StringIO.StringIO()

        if redraw:
            # Clear the screen.
            self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset, sio=sio)
            sio.write(ESC_SCROLL_UP * self.windowHeight)

            # Menu top border.
            self.MoveCursor(screenXStart, screenY, sio=sio)
            sio.write(ESC_GFX_BLUE_FG)
            sio.write(chr(218))
            sio.write(chr(196) * optionWidth)
            sio.write(chr(191))
            sio.write(ESC_GFX_OFF)

        screenY += 1

        for i, t in enumerate(options):
            hotkey, label, description = t[:3]

            if redraw:
                # Menu top space.
                self.MoveCursor(screenXStart, screenY, sio=sio)
                sio.write(ESC_GFX_BLUE_FG)
                sio.write(chr(179))
                sio.write(" " * optionWidth)
                sio.write(chr(179))
                sio.write(ESC_GFX_OFF)

            screenY += 1
            self.MoveCursor(screenXStart, screenY, sio=sio)
            sio.write(ESC_GFX_BLUE_FG)
            sio.write(chr(179))
            sio.write(ESC_GFX_OFF)
            sio.write(" ")
            if i == selected:
                sio.write(ESC_REVERSE_VIDEO_ON)
            sio.write(" %s   %-*s  - %-*s " % (hotkey, maxLabelSize, label.upper(), maxDescSize, description))
            if i == selected:
                sio.write(ESC_REVERSE_VIDEO_OFF)
            sio.write(" ")
            sio.write(ESC_GFX_BLUE_FG)
            sio.write(chr(179))
            sio.write(ESC_GFX_OFF)
            screenY += 1

        if redraw:
            # Menu bottom space.
            self.MoveCursor(screenXStart, screenY, sio=sio)
            sio.write(ESC_GFX_BLUE_FG)
            sio.write(chr(179))
            sio.write(" " * optionWidth)
            sio.write(chr(179))
            sio.write(ESC_GFX_OFF)
            screenY += 1

            # Menu bottom border.
            self.MoveCursor(screenXStart, screenY, sio=sio)
            sio.write(ESC_GFX_BLUE_FG)
            sio.write(chr(192))
            sio.write(chr(196) * optionWidth)
            sio.write(chr(217))
            sio.write(ESC_GFX_OFF)
            screenY += 1

        self.user.Write(sio.getvalue())

    def EnterGame(self):
        self.SetMode(MODE_GAMEPLAY)
        self.DisplayScreen()

    def EnterKeyboardMenu(self):
        options = []
        options.append(("L", "Laptop",    "No numeric keypad"))
        options.append(("C", "Computer",  "With a numeric keypad"))
        options.append(("Q", "Quit",      "Disconnect from the game"))
        self.DisplayMenu(MODE_KEYBOARD_MENU, options)        

    def EnterEscapeMenu(self):
        options = []
        options.append(("B", "Back",   "Return to the game"))
        options.append(("D", "Debug",  "Debug options"))
        options.append(("Q", "Quit",   "Disconnect from the game"))
        self.DisplayMenu(MODE_ESCAPE_MENU, options)

    def EnterDebugMenu(self):
        options = []
        options.append(("B", "Back",         "Return to the previous menu"))
        options.append(("C", "Client",       "Telnet client options"))
        self.DisplayMenu(MODE_DEBUG_MENU, options)

    def EnterTelnetClientMenu(self):
        options = []
        options.append(("B", "Back",         "Return to the previous menu"))
        options.append(("D", "Characters",   "Display the default character set"))
        options.append(("U", "Unicode",      "Display the unicode character set"))
        options.append(("C", "Charsets",     "Display the supported character sets"))
        self.DisplayMenu(MODE_TELNETCLIENT_MENU, options)

    def MenuActionQuit(self):
        self.stack.Pop()
        self.user.ManualDisconnection()

    def MenuActionDebug(self):
        self.EnterDebugMenu()

    def MenuActionClient(self):
        self.EnterTelnetClientMenu()

    def MenuActionBack(self):
        if self.mode == MODE_ESCAPE_MENU:
            self.EnterGame()
        elif self.mode == MODE_DEBUG_MENU:
            self.EnterEscapeMenu()
        elif self.mode == MODE_TELNETCLIENT_MENU:
            self.EnterDebugMenu()
        elif self.mode == MODE_DEBUG_DISPLAY:
            self.EnterTelnetClientMenu()

    def MenuActionLaptop(self):
        self.keyboard = "laptop"
        self.EnterGame()

    def MenuActionComputer(self):
        self.keyboard = "computer"
        self.EnterGame()

    def MenuActionUnicode(self):
        self.MenuActionCharacters(inUnicode=True)

    def MenuActionCharacters(self, charsetCode=None, inUnicode=False):
        if inUnicode:
            state = "UTF-8"
        else:
            state = "CP437"
        self.SetMode(MODE_DEBUG_DISPLAY, "Characters (%s)" % state)

        self.UpdateStatusBar("Press any key to return to the previous menu..")

        cellWidth = 6
        rowCount = self.windowHeight - 2

        sio = StringIO.StringIO()
        self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset, sio=sio)
        sio.write(ESC_SCROLL_UP * self.windowHeight)

        ranges = []
        if inUnicode:
            firstOrd, lastOrd = 0xC280, 0xC2BF
            ranges.append((firstOrd, lastOrd))

            firstOrd, lastOrd = 0xC380, 0xC3BF
            ranges.append((firstOrd, lastOrd))

            firstOrd, lastOrd = 0xC480, 0xC4BF
            ranges.append((firstOrd, lastOrd))

            sio.write("\x1b%G")
        else:
            firstOrd, lastOrd = 32, 255
            ranges.append((firstOrd, lastOrd))

            if charsetCode is not None:
                sio.write("\x1b("+ charsetCode)

        rows = []
        while len(rows) < rowCount:
            rows.append([])

        rowOffset = 0
        for i, (firstOrd, lastOrd) in enumerate(ranges):
            currentOrd = firstOrd
            while currentOrd <= lastOrd:
                if inUnicode:
                    c1 = (currentOrd >> 8) & 0xFF
                    c2 = (currentOrd >> 0) & 0xFF
                    s = "     %c%c" % (c1, c2)
                else:
                    c = self.DisplayCharacter(currentOrd, charset=charsetCode)
                    s = " %03d %s" % (currentOrd, c)

                rows[rowOffset % rowCount].append(s)
                rowOffset += 1
                currentOrd += 1

            while rowOffset % rowCount != 0:
                rows[rowOffset % rowCount].append(" " * 6)
                rowOffset += 1
 
        if inUnicode:
            linePrefix = "  "
        else:
            linePrefix = "    "
        self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset + 1, sio=sio)
        sio.write(linePrefix)
        for row in rows:
            sio.write("".join(row))
            if row is not rows[-1]:
                sio.write("\r\n")
                sio.write(linePrefix)

        if inUnicode:
            sio.write("\x1b%@")

        self.ResetCharset(sio=sio)
        self.user.Write(sio.getvalue())

    def MenuActionCharsets(self):
        self.SetMode(MODE_DEBUG_DISPLAY, "Character Sets")
        self.UpdateStatusBar("Press any key to return to the previous menu..")

        sio = StringIO.StringIO()
        self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset, sio=sio)
        sio.write(ESC_SCROLL_UP * self.windowHeight)

        firstOrd = 32
        lastOrd = 255
        # Less top spacer, bottom spacer, label line, label spacer
        rowCount = self.windowHeight - 4

        rows = []
        while len(rows) < rowCount:
            rows.append([])

        charsetCodes = [
            "\x1b(A",
            "\x1b(B",
            "\x1b(0",
            "\x1b(U",
        ]

        rowOffset = 0
        for charsetCode in charsetCodes:
            while rowOffset % rowCount != 0:
                rows[rowOffset % rowCount].append(" ")
                rowOffset += 1

            charsetRowOffset = rowOffset
            currentOrd = firstOrd
            while currentOrd <= lastOrd:
                c = self.DisplayCharacter(currentOrd, charset=charsetCode[2])
                s = "%s" % c
                if rowOffset < charsetRowOffset + rowCount:
                    s = charsetCode +"     "+ s
                rows[rowOffset % rowCount].append(s)

                rowOffset += 1
                currentOrd += 1

        titleRow = [ "    " ]
        charsetWidth = (lastOrd - firstOrd) / rowCount
        for charsetCode in charsetCodes:
            label = " %-*s" % (charsetWidth + 4 + 1, charsetCode.replace("\x1b", "ESC"))
            titleRow.append(label)
            
        self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset + 1, sio=sio)
        rows.insert(0, [])
        rows.insert(0, titleRow)
        for row in rows:
            sio.write("".join(row))
            if row is not rows[-1]:
                sio.write("\r\n")

        self.ResetCharset(sio=sio)
        self.user.Write(sio.getvalue())

    def DisplayCharacter(self, v, charset="U"):
        if v in (127, 255):
            # 127: Backspace - not suitable for display
            # 255: IAC - special telnet negotiation token
            return " "

        if charset in ("0", "1", "2", "A", "B"):
            if 128 <= v <= 159:
                return " "

        return chr(v)

