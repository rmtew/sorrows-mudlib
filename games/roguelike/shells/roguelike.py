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
        self.keyboard = None
        self.menuOptions = []
        self.menuSelection = 0

        self.status = "-"
        self.lastStatusBar = "-"

        # Send client-side information.
        self.user.connection.telneg.password_mode_on()
        self.ShowCursor(False)
        self.QueryClientName()

        self.mapArray = array.array('B', (0 for i in xrange(sorrows.world.mapHeight * sorrows.world.mapWidth)))

        self.playerX = sorrows.world.playerStartX
        self.playerY = sorrows.world.playerStartY

        rows = self.user.connection.consoleRows
        cols = self.user.connection.consoleColumns
        self.OnTerminalSizeChanged(rows, cols, redraw=False)
        self.RecalculateWorldView()

        self.charsetResetSequence = None

        self.UpdateTitle()
        self.UpdateStatusBar("Use the up and down cursor keys to choose an option, and enter to select it.")
        
        self.enteredGame = False
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
        self.ScrollWindowVertically(-1)
        self.MoveCursor(0, self.statusOffset)

    def OnTerminalSizeChanged(self, rows, columns, redraw=True):
        # Window partitioning offsets and sizes.
        self.titleOffset = 1
        self.titleWidth = columns

        self.statusOffset = rows
        self.statusWidth = columns

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

        movementShift = self.movementKeys.get(s, None)            
        if movementShift is not None:            
            newX = self.playerX + movementShift[0]
            newY = self.playerY + movementShift[1]

            # For now, can only move into empty spaces.
            tile = sorrows.world.GetTile(newX, newY)
            flags = self.mapArray[sorrows.world.mapWidth * newY + newX]
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

        self.RedrawView()

        self.UpdateTitle()
        self.UpdateStatusBar(self.lastStatusBar)

    def RedrawView(self, sio=None):
        self.UpdateLineByWorldPosition(yStart=self.worldViewY, yCount=self.windowHeight, sio=sio)
        self.UpdatePlayer(sio)

    def UpdateFoV(self, sio=None):
        self.drawRanges = {}

        def fVisited(x, y):
            self.mapArray[y * sorrows.world.mapWidth + x] |= TILE_VISIBLE

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
            tile = sorrows.world.GetTile(x, y)
            return tile not in (CHAR_TILE, " ")

        fov.fieldOfView(self.playerX, self.playerY, sorrows.world.mapWidth, sorrows.world.mapHeight, VIEW_RADIUS, fVisited, fBlocked)

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

    def UpdateLineByWorldPosition(self, xStart=None, xCount=None, yStart=None, yCount=1, sio=None, highlight=False):
        # Find the map line.
        # Find the start and end of the map line parts to examine.
        # Find the first visible and last visible characters in the given line.
        # Clear the line.
        # Display the display tiles for that character range.
        if xStart is None:
            xStart = self.worldViewX
        if xCount is None:
            xCount = self.windowWidth
        _xStart = xStart
        _xWidth = xCount

        screenY = (yStart - self.worldViewY) + self.windowYStartOffset
        for i in xrange(yCount):
            yi = (yStart + 1) + i

            if yi < 0 or yi >= sorrows.world.mapHeight:
                #self.MoveCursor(self.windowXStartOffset + self.windowWidth/2 - 1, screenY + i, sio=sio)
                #sio.write("&&&")                
                continue

            xStart = _xStart
            xWidth = _xWidth
            # Do not go outside the LHS bounds of the map.
            if xStart < 0:
                xWidth += xStart # Adjust the refreshed width for the lost area.
                xStart = 0

            xEnd = xStart + xWidth - 1
            # Do not go outside the RHS bounds of the map.
            if xEnd >= sorrows.world.mapWidth:
                xEnd = sorrows.world.mapWidth - 1

            rowOffset = yi * sorrows.world.mapWidth
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

            arr = array.array('c', (self.ViewedTile(x, yi) for x in xrange(xStart, xEnd + 1)))
            s = arr.tostring()
            if highlight:
                s = ESC_GFX_BLUE_FG + s + ESC_GFX_OFF
            if sio is None:
                self.user.Write(s)
            else:
                sio.write(s)

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
        spaceCount = self.statusWidth - len(s)
        sideSpaceCount = spaceCount / 2
        t = " " * sideSpaceCount
        s = t + s + t
        if len(s) < self.statusWidth:
            s += " " * (self.statusWidth - len(s))
        s = ESC_REVERSE_VIDEO_ON + s + ESC_REVERSE_VIDEO_OFF
        if sio is None:
            self.user.Write(s)
        else:
            sio.write(s)
        self.MoveCursor(0, self.statusOffset, clear=False, sio=sio)

    # Map Support ------------------------------------------------------------

    def ViewedTile(self, x, y):
        flags = self.mapArray[y * sorrows.world.mapWidth + x]
        if flags & TILE_VISIBLE:
            return self.GetDisplayTile(x, y)
        return " "

    def TranslateTileForDisplay(self, tile):
        dtile = displayTiles.get(tile, None)
        if dtile is not None:
            return dtile
        return tile
        
    def GetDisplayTile(self, x, y):
        if y < 0 or y >= sorrows.world.mapHeight:
            print "TILE ERROR/y", x, y
            return "?"
        if x < 0 or x >= sorrows.world.mapWidth:
            print "TILE ERROR/x", x, y
            return "?"
        tile = sorrows.world.GetTile(x, y)
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

    def ScrollWindowHorizontally(self, margin, sio=None):
        if margin < 0:
            margin = -margin
            f = self.InsertCharacters
        else:
            f = self.DeleteCharacters

        for i in xrange(self.windowHeight):
            self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset + i, sio=sio)
            f(margin, sio=sio)

    def ScrollWindowVertically(self, margin, sio=None):
        if margin < 0:
            self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset, sio=sio)
            s = ESC_SCROLL_UP * -margin
        else:
            self.MoveCursor(self.windowXStartOffset, self.windowYEndOffset, sio=sio)
            s = ESC_SCROLL_DOWN * margin
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

        xShift = 0
        if windowLeftDistance < VIEW_RADIUS:
            xShift = halfWidth - windowLeftDistance + 1
            self.worldViewX -= xShift
            # self.ScrollWindowRight(xShift, sio=sio)
            xShift = -xShift # Indicate negative movement on the horizontal axis.
        else:
            windowRightDistance = (self.worldViewX + self.windowWidth) - self.playerX
            
            if windowRightDistance <= VIEW_RADIUS:
                xShift = halfWidth - windowRightDistance - 1
                self.worldViewX += xShift

        windowUpperDistance = self.playerY - self.worldViewY
        halfHeight = self.windowHeight / 2

        # Has the player moved so their view falls outside the screen?
        # The player's line is counted in this calculation.
        yShift = 0
        if windowUpperDistance <= VIEW_RADIUS:
            # Distance needed to shift the player to the window center.
            # +1 to put them further from the side they are moving towards.
            yShift = halfHeight - windowUpperDistance + 1
            self.worldViewY -= yShift
            yShift = -yShift # Indicate negative movement on the vertical axis.
        else:
            windowLowerDistance = (self.worldViewY + self.windowHeight) - self.playerY

            # Has the player moved so their view falls outside the screen?
            # The player's line is not counted in this calculation.
            if windowLowerDistance < VIEW_RADIUS:
                # Distance needed to shift the player to the window center.
                # -1 to put them further from the side they are moving towards.
                yShift = halfHeight - windowLowerDistance - 1
                self.worldViewY += yShift

        numLinesRedrawn = 0
        if yShift:
            self.ScrollWindowVertically(yShift, sio=sio)

            # Redraw the area that moved on screen.
            if yShift < 0:
                # Account for the remaining viewed distance (less the line the player is on).
                numLinesRedrawn = (self.playerY - self.worldViewY) - 1
                self.UpdateLineByWorldPosition(yStart=self.worldViewY, yCount=numLinesRedrawn, sio=sio)
            else:
                # Account for the view range and the line the player is on.
                numLinesRedrawn = yShift + VIEW_RADIUS - 1
                self.UpdateLineByWorldPosition(yStart=self.playerY, yCount=numLinesRedrawn, sio=sio)

        if xShift:
            self.ScrollWindowHorizontally(xShift, sio=sio)
            
            if numLinesRedrawn:
                pass # TODO: Only refresh what didn't get redrawn vertically.

            # Redraw the area that moved on screen.
            if xShift < 0:
                self.UpdateLineByWorldPosition(xStart=self.worldViewX, xCount=-xShift, yStart=self.worldViewY, yCount=self.windowHeight, sio=sio)
            else:
                xStart = self.worldViewX + self.windowWidth - xShift
                self.UpdateLineByWorldPosition(xStart=xStart, xCount=xShift, yStart=self.worldViewY, yCount=self.windowHeight, sio=sio)

        # Add an FoV update over the scrolled and filled in output.
        self.UpdateFoV(sio=sio)

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
        if not self.enteredGame:
            self.lastStatusBar = "Press the Escape key to get the options menu."
            self.enteredGame = True

        self.SetMode(MODE_GAMEPLAY, "In-game")
        self.UpdateFoV()
        self.DisplayScreen()

    def EnterKeyboardMenu(self):
        options = []
        if self.enteredGame:
            options.append(("B", "Back",         "Return to the previous menu"))
        options.append(("L", "Laptop",    "No numeric keypad (yuhjklbn)"))
        options.append(("C", "Computer",  "With a numeric keypad"))
        self.DisplayMenu(MODE_KEYBOARD_MENU, options)        

    def EnterEscapeMenu(self):
        options = []
        options.append(("B", "Back",        "Return to the game"))
        options.append(("B", "Keyboard",    "Keyboard configuration"))
        options.append(("D", "Debug",       "Debug options"))
        options.append(("Q", "Quit",        "Disconnect from the game"))
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
        options.append(("C", "256Colours",   "Display xterm's 256 colours(if supported)"))
        self.DisplayMenu(MODE_TELNETCLIENT_MENU, options)

    def MenuActionQuit(self):
        self.stack.Pop()
        self.user.ManualDisconnection()

    def MenuActionKeyboard(self):
        self.EnterKeyboardMenu()

    def MenuActionDebug(self):
        self.EnterDebugMenu()

    def MenuActionClient(self):
        self.EnterTelnetClientMenu()

    def MenuActionBack(self):
        if self.mode == MODE_KEYBOARD_MENU:
            # Ignore if the player has not entered the game yet.
            if self.enteredGame:
                self.EnterEscapeMenu()
        elif self.mode == MODE_ESCAPE_MENU:
            self.EnterGame()
        elif self.mode == MODE_DEBUG_MENU:
            self.EnterEscapeMenu()
        elif self.mode == MODE_TELNETCLIENT_MENU:
            self.EnterDebugMenu()
        elif self.mode == MODE_DEBUG_DISPLAY:
            self.EnterTelnetClientMenu()

    movementKeys = {
        "\x1b[A": ( 0,-1),
        "\x1b[B": ( 0, 1),
        "\x1b[C": ( 1, 0),
        "\x1b[D": (-1, 0),
    }

    def MenuActionLaptop(self):
        self.movementKeys = self.__class__.movementKeys.copy()
        self.movementKeys.update({
            "u": ( 1,-1),
            "k": ( 0,-1),
            "y": (-1,-1),
            "l": ( 1, 0),
            "h": (-1, 0),
            "n": ( 1, 1),
            "j": ( 0, 1),
            "b": (-1, 1),
        })
        self.keyboard = "laptop"
        self.EnterGame()

    def MenuActionComputer(self):
        self.movementKeys = self.__class__.movementKeys.copy()
        self.movementKeys.update({
            "9": ( 1,-1),
            "8": ( 0,-1),
            "7": (-1,-1),
            "6": ( 1, 0),
            "4": (-1, 0),
            "3": ( 1, 1),
            "2": ( 0, 1),
            "1": (-1, 1),
        })
        self.keyboard = "computer"
        self.EnterGame()

    def MenuAction256Colours(self):
        self.SetMode(MODE_DEBUG_DISPLAY, "xterm's 256 color extension")
        self.UpdateStatusBar("Press any key to return to the previous menu..")

        sio = StringIO.StringIO()
        self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset, sio=sio)
        sio.write(ESC_SCROLL_UP * self.windowHeight)

        sio.write("\nSystem colors:\n\x1b[48;5;0m  \x1b[48;5;1m  \x1b[48;5;2m  \x1b[48;5;3m  \x1b[48;5;4m  \x1b[48;5;5m  \x1b[48;5;6m  \x1b[48;5;7m  \x1b[0m\n\x1b[48;5;8m  \x1b[48;5;9m  \x1b[48;5;10m  \x1b[48;5;11m  \x1b[48;5;12m  \x1b[48;5;13m  \x1b[48;5;14m  \x1b[48;5;15m  \x1b[0m\n\nColor cube, 6x6x6:\n\x1b[48;5;16m  \x1b[48;5;17m  \x1b[48;5;18m  \x1b[48;5;19m  \x1b[48;5;20m  \x1b[48;5;21m  \x1b[0m \x1b[48;5;52m  \x1b[48;5;53m  \x1b[48;5;54m  \x1b[48;5;55m  \x1b[48;5;56m  \x1b[48;5;57m  \x1b[0m \x1b[48;5;88m  \x1b[48;5;89m  \x1b[48;5;90m  \x1b[48;5;91m  \x1b[48;5;92m  \x1b[48;5;93m  \x1b[0m \x1b[48;5;124m  \x1b[48;5;125m  \x1b[48;5;126m  \x1b[48;5;127m  \x1b[48;5;128m  \x1b[48;5;129m  \x1b[0m \x1b[48;5;160m  \x1b[48;5;161m  \x1b[48;5;162m  \x1b[48;5;163m  \x1b[48;5;164m  \x1b[48;5;165m  \x1b[0m \x1b[48;5;196m  \x1b[48;5;197m  \x1b[48;5;198m  \x1b[48;5;199m  \x1b[48;5;200m  \x1b[48;5;201m  \x1b[0m \n\x1b[48;5;22m  \x1b[48;5;23m  \x1b[48;5;24m  \x1b[48;5;25m  \x1b[48;5;26m  \x1b[48;5;27m  \x1b[0m \x1b[48;5;58m  \x1b[48;5;59m  \x1b[48;5;60m  \x1b[48;5;61m  \x1b[48;5;62m  \x1b[48;5;63m  \x1b[0m \x1b[48;5;94m  \x1b[48;5;95m  \x1b[48;5;96m  \x1b[48;5;97m  \x1b[48;5;98m  \x1b[48;5;99m  \x1b[0m \x1b[48;5;130m  \x1b[48;5;131m  \x1b[48;5;132m  \x1b[48;5;133m  \x1b[48;5;134m  \x1b[48;5;135m  \x1b[0m \x1b[48;5;166m  \x1b[48;5;167m  \x1b[48;5;168m  \x1b[48;5;169m  \x1b[48;5;170m  \x1b[48;5;171m  \x1b[0m \x1b[48;5;202m  \x1b[48;5;203m  \x1b[48;5;204m  \x1b[48;5;205m  \x1b[48;5;206m  \x1b[48;5;207m  \x1b[0m \n\x1b[48;5;28m  \x1b[48;5;29m  \x1b[48;5;30m  \x1b[48;5;31m  \x1b[48;5;32m  \x1b[48;5;33m  \x1b[0m \x1b[48;5;64m  \x1b[48;5;65m  \x1b[48;5;66m  \x1b[48;5;67m  \x1b[48;5;68m  \x1b[48;5;69m  \x1b[0m \x1b[48;5;100m  \x1b[48;5;101m  \x1b[48;5;102m  \x1b[48;5;103m  \x1b[48;5;104m  \x1b[48;5;105m  \x1b[0m \x1b[48;5;136m  \x1b[48;5;137m  \x1b[48;5;138m  \x1b[48;5;139m  \x1b[48;5;140m  \x1b[48;5;141m  \x1b[0m \x1b[48;5;172m  \x1b[48;5;173m  \x1b[48;5;174m  \x1b[48;5;175m  \x1b[48;5;176m  \x1b[48;5;177m  \x1b[0m \x1b[48;5;208m  \x1b[48;5;209m  \x1b[48;5;210m  \x1b[48;5;211m  \x1b[48;5;212m  \x1b[48;5;213m  \x1b[0m \n\x1b[48;5;34m  \x1b[48;5;35m  \x1b[48;5;36m  \x1b[48;5;37m  \x1b[48;5;38m  \x1b[48;5;39m  \x1b[0m \x1b[48;5;70m  \x1b[48;5;71m  \x1b[48;5;72m  \x1b[48;5;73m  \x1b[48;5;74m  \x1b[48;5;75m  \x1b[0m \x1b[48;5;106m  \x1b[48;5;107m  \x1b[48;5;108m  \x1b[48;5;109m  \x1b[48;5;110m  \x1b[48;5;111m  \x1b[0m \x1b[48;5;142m  \x1b[48;5;143m  \x1b[48;5;144m  \x1b[48;5;145m  \x1b[48;5;146m  \x1b[48;5;147m  \x1b[0m \x1b[48;5;178m  \x1b[48;5;179m  \x1b[48;5;180m  \x1b[48;5;181m  \x1b[48;5;182m  \x1b[48;5;183m  \x1b[0m \x1b[48;5;214m  \x1b[48;5;215m  \x1b[48;5;216m  \x1b[48;5;217m  \x1b[48;5;218m  \x1b[48;5;219m  \x1b[0m \n\x1b[48;5;40m  \x1b[48;5;41m  \x1b[48;5;42m  \x1b[48;5;43m  \x1b[48;5;44m  \x1b[48;5;45m  \x1b[0m \x1b[48;5;76m  \x1b[48;5;77m  \x1b[48;5;78m  \x1b[48;5;79m  \x1b[48;5;80m  \x1b[48;5;81m  \x1b[0m \x1b[48;5;112m  \x1b[48;5;113m  \x1b[48;5;114m  \x1b[48;5;115m  \x1b[48;5;116m  \x1b[48;5;117m  \x1b[0m \x1b[48;5;148m  \x1b[48;5;149m  \x1b[48;5;150m  \x1b[48;5;151m  \x1b[48;5;152m  \x1b[48;5;153m  \x1b[0m \x1b[48;5;184m  \x1b[48;5;185m  \x1b[48;5;186m  \x1b[48;5;187m  \x1b[48;5;188m  \x1b[48;5;189m  \x1b[0m \x1b[48;5;220m  \x1b[48;5;221m  \x1b[48;5;222m  \x1b[48;5;223m  \x1b[48;5;224m  \x1b[48;5;225m  \x1b[0m \n\x1b[48;5;46m  \x1b[48;5;47m  \x1b[48;5;48m  \x1b[48;5;49m  \x1b[48;5;50m  \x1b[48;5;51m  \x1b[0m \x1b[48;5;82m  \x1b[48;5;83m  \x1b[48;5;84m  \x1b[48;5;85m  \x1b[48;5;86m  \x1b[48;5;87m  \x1b[0m \x1b[48;5;118m  \x1b[48;5;119m  \x1b[48;5;120m  \x1b[48;5;121m  \x1b[48;5;122m  \x1b[48;5;123m  \x1b[0m \x1b[48;5;154m  \x1b[48;5;155m  \x1b[48;5;156m  \x1b[48;5;157m  \x1b[48;5;158m  \x1b[48;5;159m  \x1b[0m \x1b[48;5;190m  \x1b[48;5;191m  \x1b[48;5;192m  \x1b[48;5;193m  \x1b[48;5;194m  \x1b[48;5;195m  \x1b[0m \x1b[48;5;226m  \x1b[48;5;227m  \x1b[48;5;228m  \x1b[48;5;229m  \x1b[48;5;230m  \x1b[48;5;231m  \x1b[0m \n\nGrayscale ramp:\n\x1b[48;5;232m  \x1b[48;5;233m  \x1b[48;5;234m  \x1b[48;5;235m  \x1b[48;5;236m  \x1b[48;5;237m  \x1b[48;5;238m  \x1b[48;5;239m  \x1b[48;5;240m  \x1b[48;5;241m  \x1b[48;5;242m  \x1b[48;5;243m  \x1b[48;5;244m  \x1b[48;5;245m  \x1b[48;5;246m  \x1b[48;5;247m  \x1b[48;5;248m  \x1b[48;5;249m  \x1b[48;5;250m  \x1b[48;5;251m  \x1b[48;5;252m  \x1b[48;5;253m  \x1b[48;5;254m  \x1b[48;5;255m  \x1b[0m\n".replace("\n", "\r\n "))
        self.user.Write(sio.getvalue())

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

