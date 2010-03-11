import random, array, math, StringIO
import uthread, fov
from mudlib import Shell, InputHandler


EC_CLEAR_LINE        = "\x1b[2K"
EC_CLEAR_SCREEN      = "\x1b[2J"
EC_HOME_CURSOR       = "\x1b[1;1H"
EC_RESET_TERMINAL    = "\x1bc"
EC_REVERSE_VIDEO_ON  = "\x1b[7m"
EC_REVERSE_VIDEO_OFF = "\x1b[27m"
EC_SCROLL_UP         = "\x1bM"
EC_SCROLL_DOWN       = "\x1bD"
EC_ERASE_DOWN        = "\x1b[J"
EC_ERASE_UP          = "\x1b[1J"

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
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXX     X     XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXX     X     XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXX     X     XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     XXXXXDXXXXXDXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX           D              D XXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXX     XXXXXDXXXXXDXXXX XXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     XXXXX XXXXX     X     X  X   XXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  @  XXXXX XXXXX     X     X XX   XXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     XXXXX XXXXX     X     X X    XXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXX XXXXDXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXX      XXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
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
    CHAR_TILE: ".",
    WALL_TILE: chr(0xB0),
    FLOOR_TILE: ".",
    DOOR_TILE: "D",
}

TILE_VISIBLE = 1
TILE_OPEN = 2

VIEW_RADIUS = 4

class RoguelikeShell(Shell):
    def Setup(self, stack):
        Shell.Setup(self, stack)

        handler = InputHandler()
        handler.Setup(self, self.ReceiveInput, None, 0)
        stack.Push(handler)

        self.oldOptionLineMode = self.user.connection.optionLineMode
        self.user.connection.optionLineMode = False

        self.status = "-"
        self.lastStatusBar = "-"

        self.user.connection.telneg.password_mode_on()
        self.ShowCursor(False)

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
        self.OnTerminalSizeChanged(rows, cols)
        self.RecalculateWorldView()

        self.DisplayScreen()

    # ------------------------------------------------------------------------

    def OnRemovalFromStack(self):
        self.user.connection.optionLineMode = self.oldOptionLineMode
        self.user.connection.telneg.request_will_echo()
        self.user.Write(EC_RESET_TERMINAL)
        self.ScrollWindowUp()
        self.MoveCursor(0, self.statusOffset)

    def OnTerminalSizeChanged(self, rows, columns):
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

        self.DisplayScreen()

    def ReceiveInput(self, s):
        self._ReceiveInput(s)

    def _ReceiveInput(self, s):
        if s == chr(27): # Escape
            self.stack.Pop()
            self.user.ManualDisconnection()
            return

        if s == chr(5):
            # Putty responds to CTRL-E with its ID.
            self.user.Write(chr(5))
        elif s == chr(18):
            self.lastStatusBar = " Screen refreshed"
            self.DisplayScreen()

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
                sio = StringIO.StringIO()
                tile = self.GetDisplayTile(self.playerX, self.playerY)
                self.UpdateViewByWorldPosition(self.playerX, self.playerY, tile, sio=sio)

                self.playerX = newX
                self.playerY = newY

                if self.playerX - self.worldViewX < VIEW_RADIUS:
                    xShift = self.windowWidth - self.playerX - self.worldViewX
                    self.worldViewX += xShift
                elif self.worldViewX + self.windowWidth - self.playerX < VIEW_RADIUS:
                    xShift = self.windowWidth - self.worldViewX + self.windowWidth - self.playerX
                    self.worldViewX += xShift

                scrollDirection = "    "
                udistance = self.playerY - self.worldViewY
                ldistance = 99
                worldViewLowerY = self.worldViewY + self.windowHeight
                if udistance <= VIEW_RADIUS:
                    yShift = (self.windowHeight / 2) - udistance + 1
                    self.worldViewY -= yShift
                    self.ScrollWindowUp(yShift+2, sio=sio)
                    scrollDirection = "UP  "

                    # Account for the view range and the line the player is on.
                    blankLines = (self.playerY - self.worldViewY) - VIEW_RADIUS - 1
                    self.UpdateLineByWorldPosition(self.worldViewY, cnt=blankLines, sio=sio)
                else:
                    ldistance = worldViewLowerY - self.playerY
                    if ldistance < VIEW_RADIUS:
                        yShift = (self.windowHeight / 2) - ldistance - 1
                        self.worldViewY += yShift
                        self.ScrollWindowDown(yShift, sio=sio)
                        sio.write(EC_ERASE_DOWN)
                        scrollDirection = "DOWN"

                        # Account for the view range and the line the player is on.
                        blankLines = yShift
                        self.UpdateLineByWorldPosition(self.playerY + VIEW_RADIUS, cnt=blankLines, sio=sio)

                args = scrollDirection, self.playerX, self.playerY, self.worldViewX, self.worldViewY, worldViewLowerY
                self.UpdateStatusBar("%s [%03d %03d] [%03d %03d-%03d]" % args, sio=sio)

                self.UpdateView(sio=sio)

                self.user.Write(sio.getvalue())
            return

        if False:
            # Kept this in case I wanted to preserve the hard limits,
            # should the tile check fail.
            if s == "\x1b[A": # Up cursor key.
                if self.playerY <= self.titleOffset + 1:
                    pass # skip
            elif s == "\x1b[B": # Down cursor key.
                if self.playerY >= self.statusOffset - 1:
                    pass # skip
            elif s == "\x1b[C": # Right cursor key.
                if self.playerX >= self.user.connection.consoleColumns:        
                    pass # skip
            elif s == "\x1b[D": # Left cursor key.
                if self.playerX <= 1:        
                    pass # skip

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
        self.user.Write(EC_CLEAR_SCREEN)

        self.UpdateView()

        self.UpdateTitle()
        self.UpdateStatusBar(self.lastStatusBar)

    def GetTile(self, x, y):
        return self.mapRows[y][x]

    def TranslateTileForDisplay(self, tile):
        dtile = displayTiles.get(tile, None)
        if dtile is not None:
            return dtile
        return tile
        
    def GetDisplayTile(self, x, y):
        tile = self.mapRows[y][x]
        return self.TranslateTileForDisplay(tile)

    def UpdateView(self, sio=None):
        # REUSE?  Useful for centering of the world or view or something.

        # TODO: BROKEN OR IN NEED OF REFACTORING
        #
        # - The positions should be stored on the objects, not on this object.
        #   body.position = (X, Y)
        # - Movement of the player should not update the view, but should rather
        #   simply reset the position they moved from, and update the position
        #   they moved to.

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
            xEnd = xStart + self.windowWidth - 1

            rowOffset = yi * self.mapWidth
            for x in range(xStart, xEnd + 1):
                flags = self.mapArray[rowOffset + x]
                if flags & TILE_VISIBLE:
                    xStart = x
                    break
            else:
                pass

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

    def ViewedTile(self, x, y, flag=False):
        flags = self.mapArray[y * self.mapWidth + x]
        if flags & TILE_VISIBLE:
            return self.GetDisplayTile(x, y)
        return " "

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

    def UpdateTitle(self):
        pre = EC_HOME_CURSOR
        
        left = "  "+ sorrows.data.config.identity.name
        right = self.status +"  "

        self.user.Write(pre)
        self.user.Write(EC_REVERSE_VIDEO_ON + left + (" " * (self.user.connection.consoleColumns - len(left) - len(right))) + right + EC_REVERSE_VIDEO_OFF)

    def UpdateStatusBar(self, s, sio=None):
        self.lastStatusBar = s

        self.MoveCursor(0, self.statusOffset, clear=True, sio=sio)
        s = EC_REVERSE_VIDEO_ON + s + (" " * (self.user.connection.consoleColumns - len(s))) + EC_REVERSE_VIDEO_OFF
        if sio is None:
            self.user.Write(s)
        else:
            sio.write(s)
        self.MoveCursor(0, self.statusOffset, clear=False, sio=sio)

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
            s += EC_CLEAR_LINE
        if sio is None:
            self.user.Write(s)
        else:
            sio.write(s)

    def SaveCursorPosition(self):
        self.user.Write("\x1b[s")
        
    def RestoreCursorPosition(self):
        self.user.Write("\x1b[u")

    # ANSI Scrolling ---------------------------------------------------------

    def SetScrollingRows(self, yLow, yHigh):
        self.user.Write("\x1b[%d;%dr" % (yLow, yHigh))

    def ResetScrollingRows(self):
        self.user.Write("\x1b[r")

    def ScrollWindowUp(self, cnt=1, sio=None):
        self.MoveCursor(0, self.windowYStartOffset + 2, sio=sio)
        s = EC_SCROLL_UP * cnt
        if sio is None:
            self.user.Write(s)
        else:
            sio.write(s)

    def ScrollWindowDown(self, cnt=1, sio=None):
        self.MoveCursor(0, self.windowYEndOffset, sio=sio)
        s = EC_SCROLL_DOWN * cnt
        if sio is None:
            self.user.Write(s)
        else:
            sio.write(s)

    def InsertCharacters(self, times=1):
        self.user.Write("\x1b[%d@" % times)

    def DeleteCharacters(self, times=1):
        self.user.Write("\x1b[%dP" % times)

    # ANSI Attribute ---------------------------------------------------------

    def RepeatLastCharacter(self, times=1):
        self.user.Write("\x1b[%db" % times)

    def EraseCharacters(self, times=1):
        self.user.Write("\x1b[%dX" % times)
