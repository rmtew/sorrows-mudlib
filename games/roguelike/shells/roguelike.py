## COMMODITY TASKS
#
# - NPC logic.  This is very simple now, but taking this further would be
#   something to think about.
#
# - Connection level changes:
#   - Ability to set a per-packet delay before sending to user.
#   - Ability to set a per-character delay before sending to user.
#
# - Windows Telnet:
#   - Why are escape characters not working.
#   - What characters should be displayed when unicode characters cannot
#     be encoded as CP437.
# ** Putty is currently the preferrred and working client.

## LUXURY TASKS
#
# - Optimal rendering system.  At the moment, emphasis is done on a need
#   basis, rather than a per-tile basis.  Colouring should be done in much
#   the same way.  In general, rendering updates should be constructed in
#   a way where it updates are smoothly and as cleanly to the user as possible.
#
# - It should be possible to move a cursor around the map and select a tile
#   has been visited.  This might be used for an automove mode, where the
#   player then automatically paths to the selected tile.
#
# - Explosion.  Fire should spread out and channel down available routes of
#   escape, the more avenues of escape, the shorter it takes to spread out.
#   If blocked by non-permanent barriers (doors for instance), it should if
#   there is no other route of escape break or remove them from their
#   hinges.  If no route of escape, should cause damage to ceiling, walls
#   or floors.  Use of colour.. like red and oranges.
#
# - Door logic.  Open.  Closed.  Locked.  Closed but not visited, and no
#   visual indication of lock status.  Closed and visited, and visual
#   indication of lock status.
#
# - Clean up use of ViewedTileRange() so it can be degeneratorised.
#

import random, array, math, StringIO, time, stackless
from stacklesslib.main import sleep as tasklet_sleep
import fov
from mudlib import Shell, InputHandler

# ASCII CODES -----------------------------------------------------------------

# Escape codes.

ESC = chr(27)

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
ESC_BOLD              = "\x1b[1m"
ESC_GFX_BLUE_FG       = "\x1b[34m"
ESC_RESET_ATTRS       = "\x1b[0m"
ESC_NORMAL            = "\x1b[22m"

# Escape termination characters.
#
# The rule for detecting a full escape sequence is to keep reading characters
# after escape until any character from 'a'-'z', '{', '|', '@', 'A'-'Z' is
# encountered.
#

ESC_TERMINATORS = set()
for v in range(97, 124+1):
    ESC_TERMINATORS.add(chr(v))
for v in range(64, 90+1):
    ESC_TERMINATORS.add(chr(v))

# Control codes.

CTRL_E                = chr(5)  # ENQ

# Escape codes.

ESC_UTF8_CHARSET =      "\x1b%G"
ESC_DEFAULT_CHARSET =   "\x1b%@"
ESC_SCO_CHARSET =       "\x1b(U"


CHAR_TILE =  "@"
WALL_TILE =  "X"
WALL_TILE1 = "1"
WALL_TILE2 = "2"
FLOOR_TILE = " "
DOOR_TILE =  "D"
CUBE_TILE =  "C"

charMap = {    
    "unicode" : {
        # Map character mappings.
        WALL_TILE1: u"\u2591", # Light shade.
        WALL_TILE2: u"\u2592", # Medium shade.
        WALL_TILE:  u"\u2593", # Dark shade.
        FLOOR_TILE: u"\xB7",   # Middle dot.
        DOOR_TILE:  u"\u25A0", # Black square.
        CUBE_TILE:  u"\u2588", # Full block.
        CHAR_TILE:  u"@",

        # Line-drawing characters.
        "light-horizontal":         u"\u2500",
        "light-vertical":           u"\u2502",
        "light-down-and-right":     u"\u250C",
        "light-down-and-left":      u"\u2510",
        "light-up-and-right":       u"\u2514",
        "light-up-and-left":        u"\u2518",
        "full-block":               u"\u2588",
        "medium-shade":             u"\u2592",
        "black-square":             u"\u25A0",
        "white-square":             u"\u25A1",
    }
}

def CHARACTERS(key, encoding):
    encodingCharMap = charMap.get(encoding)
    # Cache the characters in the given encoding, if they already are not.
    if not encodingCharMap:
        encodingCharMap = {}
        for key_, value_ in charMap["unicode"].iteritems():
            encodingCharMap[key_] = value_.encode(encoding, "ignore")
        charMap[encoding] = encodingCharMap
    if key in encodingCharMap:
        return encodingCharMap[key]
    return key
        
TILE_SEEN = 1
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

MSG_PRESS_ANY_KEY_TO_RETURN = "Press any key to return to the previous menu.."
MSG_PRESS_ESCAPE_FOR_OPTIONS = "Press the Escape key to get the options menu."



class RoguelikeShell(Shell):
    gameKeyMap = None

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
        self.inputBuffer = ""
        self.escapeTasklet = None

        self.status = "-"
        self.lastStatusBar = "-"

        # Send client-side information.
        # self.user.connection.telneg.will_echo()
        # self.user.connection.telneg.do_sga()
        
        self.ShowCursor(False)
        self.QueryClientName()

        self.mapArray = array.array('B', (0 for i in xrange(sorrows.world.mapHeight * sorrows.world.mapWidth)))
        self.drawRangesNew = {}
        self.drawRangesOld = {}

        rows = self.user.connection.consoleRows
        cols = self.user.connection.consoleColumns
        self.OnTerminalSizeChanged(cols, rows, redraw=False)
        self.RecalculateWorldView()

        self.charsetResetSequence = None
        self.charsetEncoding = "cp437"

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
            self.charsetEncoding = "utf8"
            self.charsetResetSequence = ESC_UTF8_CHARSET # ESC_SCO_CHARSET
            self.ResetCharset()

    def SetMode(self, mode, status=None):
        if status is None:
            status = MODE_NAMES.get(mode, None)
        if status is not None:
            self.UpdateTitle(status)
        self.mode = mode

    # Events ------------------------------------------------------------------

    def OnRemovalFromStack(self):
        if self.user.connection.connected:
            self.user.connection.optionLineMode = self.oldOptionLineMode
            self.user.connection.telneg.will_echo()
            self.user.Write(ESC_RESET_TERMINAL)
            self.ScrollWindowVertically(-1)
            self.MoveCursor(0, self.statusOffset)
        Shell.OnRemovalFromStack(self)

    def OnTerminalSizeChanged(self, columns, rows, redraw=True):
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

    def ReceiveInput(self, s, flush=False):
        if False:
            cnt = getattr(self, "xxx", 1)
            self.xxx = cnt + 1
            print cnt, "** ReceiveInput", [ ord(c) for c in s ], flush
 
        if len(self.inputBuffer):
            s = self.inputBuffer + s
            self.inputBuffer = ""

        escapeTasklet = self.escapeTasklet
        self.escapeTasklet = None

        if not flush:
            if escapeTasklet:
                escapeTasklet.kill()

            if s[0] == ESC:
                if len(s) == 1:
                    self.inputBuffer = s

                    # A lone escape can be one of two things:
                    # - An actual press of the escape key.
                    # - The start of an escape sequence.
                    # The way to differentiate is to use a timeout to wait for
                    # the rest of the escape sequence, and if nothing arrives 
                    # to assume it is a keypress.
                    self.escapeTasklet = stackless.tasklet(self.ReceiveInput_EscapeTimeout)()
                    return

                if s[1] != '[':
                    idx = s.find(ESC, 1)
                    if idx == -1:
                        self.DispatchInputSequence(s)
                        return
                    self.DispatchInputSequence(s[:idx])
                    self.ReceiveInput(s[idx:])
                    return

                for i, c in enumerate(s):
                    if c in ESC_TERMINATORS:
                        self.DispatchInputSequence(s[:i+1])
                        remainingInput = s[i+1:]
                        if remainingInput:
                            self.ReceiveInput(remainingInput)
                        return

                self.inputBuffer = s
                return

        idx = s.find(ESC)
        if idx == -1 or idx == 0:
            self.DispatchInputSequence(s)
        else:
            self.DispatchInputSequence(s[:idx])
            self.ReceiveInput(s[idx:])
        # print "** ReceiveInput - DONE"

    def ReceiveInput_EscapeTimeout(self):
        tasklet_sleep(0.1)
        self.ReceiveInput("", flush=True)

    def DispatchInputSequence(self, s):
        # print "** DispatchInputSequence", [ ord(c) for c in s ]

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
            playerX, playerY = self.user.body.GetPosition()

            windowUpperDistance = playerY - self.worldViewY
            worldViewLowerY = self.worldViewY + self.windowHeight
            windowLowerDistance = worldViewLowerY - playerY

            sio = StringIO.StringIO()
            self.SaveCursorPosition(sio=sio)
            args = playerX, playerY, self.worldViewX, self.worldViewY, worldViewLowerY
            self.UpdateStatusBar(" [%03d %03d] [%03d %03d-%03d]" % args, sio=sio)
            self.RestoreCursorPosition(sio=sio)
            self.user.Write(sio.getvalue())
            return
        elif s == chr(18):
            self.lastStatusBar = " Screen refreshed"
            self.DisplayScreen()
            return

        actionKey = self.gameKeyMap.get(s)
        if actionKey is not None:
            actionName, args = self.actionMap[actionKey]
            f = getattr(self, "GameAction"+ actionName, None)
            if f is not None:
                f(*args)
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
        
        if self.user.body:
            playerX, playerY = self.user.body.GetPosition()

            # World view offsets and sizes.
            self.worldViewX = playerX - halfWidth
            self.worldViewY = playerY - halfHeight

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
        self.drawRangesOld = self.drawRangesNew
        self.drawRangesNew = {}

        def fVisited(x, y):
            if x < self.worldViewX or x > self.worldViewX + self.windowWidth:
                return
            if y < self.worldViewY or y > self.worldViewY + self.windowHeight+1:
                return

            self.AddTileBits(x, y, TILE_SEEN)
            
            if y in self.drawRangesNew:
                minX, maxX = self.drawRangesNew[y]
                self.drawRangesNew[y] = [ min(x, minX), max(x, maxX) ]
            else:
                self.drawRangesNew[y] = [ x, x ]

        def fBlocked(x, y):
            return sorrows.world.IsLocationOpaque(x, y)
            #    if self._GetTileBits(x, y) & TILE_OPEN:
            #        return False
            #    return True
            #return False

        playerX, playerY = self.user.body.GetPosition()
        fov.fieldOfView(playerX, playerY, sorrows.world.mapWidth, sorrows.world.mapHeight, VIEW_RADIUS, fVisited, fBlocked)

        # The update ranges should cover the old and the new field of views.
        # Tiles outside the new field of view (and in the old) will get
        # deemphasised.  And tiles within the new FoV will get the opposite.
        drawRanges = self.drawRangesOld.copy()
        for y, t1 in self.drawRangesNew.iteritems():
            if y not in drawRanges:
                drawRanges[y] = t1
            else:
                t0 = drawRanges[y]
                if t0 != t1:
                    drawRanges[y] = [ min(t0[0], t1[0]), max(t0[1], t1[1]) ]

        sio_ = StringIO.StringIO() if sio is None else sio

        for y, (minX, maxX) in drawRanges.iteritems():
            vMinX = (minX - self.worldViewX) + 1
            vMaxX = (maxX - self.worldViewX) + 1
            if vMinX < 1 or vMaxX > self.windowWidth:
                continue

            vy = (y - self.worldViewY) + 1
            if vy < self.windowYStartOffset or vy > self.windowYEndOffset:
                continue

            self.MoveCursor(vMinX, vy, sio=sio_)
            for s in self.ViewedTileRange(minX, maxX, y):
                sio_.write(s)
            # arr = array.array('c', (c for c in self.ViewedTileRange(minX, maxX, y)))
            #sio_.write(arr.tostring())

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
                if flags & TILE_SEEN:
                    xStart = x
                    break

            for x in range(xEnd, xStart - 1, -1):
                flags = self.mapArray[rowOffset + x]
                if flags & TILE_SEEN:
                    xEnd = x
                    break

            screenX = (xStart - self.worldViewX) + self.windowXStartOffset
            self.MoveCursor(screenX, screenY + i, sio=sio)

            s = ""
            for t in self.ViewedTileRange(xStart, xEnd, yi):
                s += t
            # arr = array.array('c', (c for c in self.ViewedTileRange(xStart, xEnd, yi)))
            #s = arr.tostring()
            if highlight:
                s = ESC_GFX_BLUE_FG + s + ESC_RESET_ATTRS
            self.user.Write(s) if sio is None else sio.write(s)

    def UpdateViewByWorldPosition(self, x, y, c, sio=None):
        vx = (x - self.worldViewX) + 1
        vy = (y - self.worldViewY) + 1
        self.MoveCursor(vx, vy, sio=sio)
        if sio is None:
            self.user.Write(c)
        else:
            sio.write(c)

    def UpdatePlayer(self, sio=None):
        playerX, playerY = self.user.body.GetPosition()
        tile = sorrows.world.GetTile(playerX, playerY)
        s = self.TileColouring(tile, emphasis=True)
        self.UpdateViewByWorldPosition(playerX, playerY, s, sio=sio)

    def UpdateTitle(self, newStatus=None):
        pre = ESC_HOME_CURSOR

        if newStatus is not None:
            self.status = newStatus
        
        leftText = "  "+ sorrows.data.config.identity.name
        rightText = self.status +"  "
        centerText = self.user.name
        
        numUnusedChars = self.user.connection.consoleColumns - len(leftText) - len(centerText) - len(rightText)
        leftFiller = " " * (numUnusedChars / 2)
        rightFiller = " " * (numUnusedChars - len(leftFiller))

        self.user.Write(pre)
        self.user.Write(ESC_REVERSE_VIDEO_ON + leftText + leftFiller + centerText + rightFiller + rightText + ESC_REVERSE_VIDEO_OFF)

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

    # Gameplay Support --------------------------------------------------------

    def OnObjectMoved(self, object_, oldPosition, newPosition):
        if not self.enteredGame or self.mode != MODE_GAMEPLAY:
            return

        if object_ is self.user.body:
            # print id(self), "I MOVED TO", newPosition
            self.OnMovement(*newPosition)
            return

        sio = StringIO.StringIO()
        if oldPosition is not None and self.IsTileInFoV(*oldPosition):
            tile = self.ViewedTile(*oldPosition)
            self.UpdateViewByWorldPosition(oldPosition[0], oldPosition[1], tile, sio)
        if newPosition is not None and self.IsTileInFoV(*newPosition):
            tile = self.ViewedTile(*newPosition)
            self.UpdateViewByWorldPosition(newPosition[0], newPosition[1], tile, sio)
        if sio.tell() > 0:
            self.user.Write(sio.getvalue())

    def OnMovement(self, playerX, playerY):
        sio = StringIO.StringIO()

        windowLeftDistance = playerX - self.worldViewX
        halfWidth = self.windowWidth / 2

        xShift = 0
        if windowLeftDistance < VIEW_RADIUS:
            xShift = halfWidth - windowLeftDistance + 1
            self.worldViewX -= xShift
            # self.ScrollWindowRight(xShift, sio=sio)
            xShift = -xShift # Indicate negative movement on the horizontal axis.
        else:
            windowRightDistance = (self.worldViewX + self.windowWidth) - playerX
            
            if windowRightDistance <= VIEW_RADIUS:
                xShift = halfWidth - windowRightDistance - 1
                self.worldViewX += xShift

        windowUpperDistance = playerY - self.worldViewY
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
            windowLowerDistance = (self.worldViewY + self.windowHeight) - playerY

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
                numLinesRedrawn = (playerY - self.worldViewY) - 1
                self.UpdateLineByWorldPosition(yStart=self.worldViewY, yCount=numLinesRedrawn, sio=sio)
            else:
                # Account for the view range and the line the player is on.
                numLinesRedrawn = yShift + VIEW_RADIUS - 1
                self.UpdateLineByWorldPosition(yStart=playerY, yCount=numLinesRedrawn, sio=sio)

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

    def GameActionMovement(self, xOffset, yOffset):
        playerX, playerY = self.user.body.GetPosition()
        newPosition = playerX + xOffset, playerY + yOffset
        sorrows.world.MoveObject(self.user.body, newPosition)

    def GameActionExplosion(self):
        if getattr(self, "fireSource", None) is None:
            import game.services
            ob = self.fireSource = game.services.FireSource()
            sorrows.world._MoveObject(ob, self.user.body.GetPosition(), force=True)
        else:
            ob = self.fireSource
            self.fireSource = None
            sorrows.world._MoveObject(ob, None)

    # Map Support ------------------------------------------------------------

    def _SetTileBits(self, x, y, bits):
        self.mapArray[y * sorrows.world.mapWidth + x] = bits

    def _GetTileBits(self, x, y):
        return self.mapArray[y * sorrows.world.mapWidth + x]

    def SetTileBits(self, x, y, bits):
        sorrows.world.CheckBoundaries(x, y)
        self._SetTileBits(x, y, bits)

    def GetTileBits(self, x, y, mask=None):
        sorrows.world.CheckBoundaries(x, y)
        if mask is None:
            return self._GetTileBits(x, y)
        return self._GetTileBits(x, y) & mask

    def AddTileBits(self, x, y, bits):
        sorrows.world.CheckBoundaries(x, y)
        bits |= self._GetTileBits(x, y)
        self._SetTileBits(x, y, bits)
        return bits

    def RemoveTileBits(self, x, y, mask):
        sorrows.world.CheckBoundaries(x, y)
        bits = self._GetTileBits(x, y)
        bits &= ~mask
        self._SetTileBits(x, y, bits)
        return bits

    # Map display support ----------------------------------------------------

    def IsTileInFoV(self, x, y):
        if y in self.drawRangesNew:
            minX, maxX = self.drawRangesNew[y]
            if x >= minX and x <= maxX:
                return True
        return False

    def ViewedTileRange(self, minX, maxX, y):
        l = []
        if y in self.drawRangesNew:
            minFovX, maxFovX = self.drawRangesNew[y]
            while True:
                # Handle the LHS of FoV case.
                if minX < minFovX:
                    r = min(maxX, minFovX-1)
                    l.append((False, minX, r))
                    if r == maxX:
                        break
                    minX = r+1

                # Handle the inside FoV case.
                if minX <= maxFovX:
                    r = min(maxX, maxFovX)
                    l.append((True, minX, r))
                    if r == maxX:
                        break
                    minX = r+1

                # Handle the RHS of FoV case.
                l.append((False, minX, maxX))
                break            
        else:
            l.append((False, minX, maxX))

        # Draw row tiles in order, but batched depending on whether they are
        # emphasised or not.
        for emphasis, minX, maxX in l:
            if emphasis:
                for c in ESC_BOLD:
                    yield c

            x = minX
            while x <= maxX:
                tile = self.GetDisplayTileInfo(x, y, not emphasis)
                if tile is None:
                    yield " "
                else:
                    yield self.TileColouring(tile)
                x += 1
            
            if emphasis:
                for c in ESC_NORMAL:
                    yield c

    def ViewedTile(self, x, y):
        emphasis = self.IsTileInFoV(x, y)
        tile = self.GetDisplayTileInfo(x, y, not emphasis)
        if tile is not None:
            return self.TileColouring(tile, emphasis)
        return " "

    def TileColouring(self, tile, emphasis=False):
        # print "TileColouring", "'%s'" % tile.character, tile.fgColour, tile.bgColour
        s = ""
        if tile.fgColour:
            s += "\x1b[3%dm" % tile.fgColour
        if tile.bgColour:
            s += "\x1b[4%dm" % tile.bgColour
        if emphasis:
            s += ESC_BOLD
        s += CHARACTERS(tile.character, self.charsetEncoding)
        if emphasis:
            s += ESC_NORMAL
        if tile.fgColour:
            s += "\x1b[3%dm" % 7    # White text.
        if tile.bgColour:
            s += "\x1b[4%dm" % 0    # Black background.
        return s

    def GetDisplayTileInfo(self, x, y, mapOnly=True):
        if self.GetTileBits(x, y, TILE_SEEN):
            # Translate the map tile to what should actually be displayed.
            if mapOnly:
                rawTile = sorrows.world.GetMapTile((x, y))
            else:
                rawTile = sorrows.world.GetTile(x, y)
            if not rawTile.isMarker:
                return rawTile

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
            sio.write(CHARACTERS("light-down-and-right", self.charsetEncoding))
            sio.write(CHARACTERS("light-horizontal", self.charsetEncoding) * optionWidth)
            sio.write(CHARACTERS("light-down-and-left", self.charsetEncoding))
            sio.write(ESC_RESET_ATTRS)

        screenY += 1

        for i, t in enumerate(options):
            hotkey, label, description = t[:3]

            if redraw:
                # Menu top space.
                self.MoveCursor(screenXStart, screenY, sio=sio)
                sio.write(ESC_GFX_BLUE_FG)
                sio.write(CHARACTERS("light-vertical", self.charsetEncoding))
                sio.write(" " * optionWidth)
                sio.write(CHARACTERS("light-vertical", self.charsetEncoding))
                sio.write(ESC_RESET_ATTRS)

            screenY += 1
            self.MoveCursor(screenXStart, screenY, sio=sio)
            sio.write(ESC_GFX_BLUE_FG)
            sio.write(CHARACTERS("light-vertical", self.charsetEncoding))
            sio.write(ESC_RESET_ATTRS)
            sio.write(" ")
            if i == selected:
                sio.write(ESC_REVERSE_VIDEO_ON)
            sio.write(" %s   %-*s  - %-*s " % (hotkey, maxLabelSize, label.upper(), maxDescSize, description))
            if i == selected:
                sio.write(ESC_REVERSE_VIDEO_OFF)
            sio.write(" ")
            sio.write(ESC_GFX_BLUE_FG)
            sio.write(CHARACTERS("light-vertical", self.charsetEncoding))
            sio.write(ESC_RESET_ATTRS)
            screenY += 1

        if redraw:
            # Menu bottom space.
            self.MoveCursor(screenXStart, screenY, sio=sio)
            sio.write(ESC_GFX_BLUE_FG)
            sio.write(CHARACTERS("light-vertical", self.charsetEncoding))
            sio.write(" " * optionWidth)
            sio.write(CHARACTERS("light-vertical", self.charsetEncoding))
            sio.write(ESC_RESET_ATTRS)
            screenY += 1

            # Menu bottom border.
            self.MoveCursor(screenXStart, screenY, sio=sio)
            sio.write(ESC_GFX_BLUE_FG)
            sio.write(CHARACTERS("light-up-and-right", self.charsetEncoding))
            sio.write(CHARACTERS("light-horizontal", self.charsetEncoding) * optionWidth)
            sio.write(CHARACTERS("light-up-and-left", self.charsetEncoding))
            sio.write(ESC_RESET_ATTRS)
            screenY += 1

        self.user.Write(sio.getvalue())

    def EnterGame(self):
        self.lastStatusBar = MSG_PRESS_ESCAPE_FOR_OPTIONS

        if not self.enteredGame:
            sorrows.world.OnUserEntersGame(self.user, self.user.body)
            self.RecalculateWorldView()
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
        options.append(("K", "Keyboard",    "Keyboard configuration"))
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
        options.append(("C", "Characters",   "Display the default character set"))
        options.append(("U", "Unicode",      "Display the unicode character set"))
        options.append(("K", "Charsets",     "Display the supported character sets"))
        options.append(("X", "256Colours",   "Display xterm's 256 colours (if supported)"))
        options.append(("D", "Dithering",    "Display colours dithered"))
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

    actionMap = {
        "move-nw":      ("Movement", (-1,-1)),
        "move-n":       ("Movement", ( 0,-1)),
        "move-ne":      ("Movement", ( 1,-1)),
        "move-w":       ("Movement", (-1, 0)),
        "move-e":       ("Movement", ( 1, 0)),
        "move-sw":      ("Movement", (-1, 1)),
        "move-s":       ("Movement", ( 0, 1)),
        "move-se":      ("Movement", ( 1, 1)),

        "explosion":    ("Explosion", ()),
    }

    gameplayKeyset = {
        "f":            "explosion",
    }

    cursorMovementKeyset = {
        "\x1b[A": "move-n",
        "\x1b[B": "move-s",
        "\x1b[C": "move-e",
        "\x1b[D": "move-w",
    }

    numericMovementKeyset = {
        "9": "move-ne",
        "8": "move-n",
        "7": "move-nw",
        "6": "move-e",
        "4": "move-w",
        "3": "move-se",
        "2": "move-s",
        "1": "move-sw",
    }

    laptopMovementKeyset = {
        "u": "move-ne",
        "k": "move-n",
        "y": "move-nw",
        "l": "move-e",
        "h": "move-w",
        "n": "move-se",
        "j": "move-s",
        "b": "move-sw",
    }

    def BuildGameKeyMap(self):
        self.gameKeyMap = {}
        self.gameKeyMap.update(self.cursorMovementKeyset)
        self.gameKeyMap.update(self.gameplayKeyset)

    def ExtendGameKeyMap(self, extendKeyMap):
        self.gameKeyMap.update(extendKeyMap)

    def MenuActionLaptop(self):
        self.BuildGameKeyMap()
        self.ExtendGameKeyMap(self.laptopMovementKeyset)
        self.keyboard = "laptop"
        self.EnterGame()

    def MenuActionComputer(self):
        self.BuildGameKeyMap()
        self.ExtendGameKeyMap(self.numericMovementKeyset)
        self.keyboard = "computer"
        self.EnterGame()

    def MenuAction256Colours(self):
        self.SetMode(MODE_DEBUG_DISPLAY, "xterm's 256 colour extension")
        self.UpdateStatusBar(MSG_PRESS_ANY_KEY_TO_RETURN)

        sio = StringIO.StringIO()
        self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset, sio=sio)
        sio.write(ESC_SCROLL_UP * self.windowHeight)

        sio.write("\nSystem colors:\n\x1b[48;5;0m  \x1b[48;5;1m  \x1b[48;5;2m  \x1b[48;5;3m  \x1b[48;5;4m  \x1b[48;5;5m  \x1b[48;5;6m  \x1b[48;5;7m  \x1b[0m\n\x1b[48;5;8m  \x1b[48;5;9m  \x1b[48;5;10m  \x1b[48;5;11m  \x1b[48;5;12m  \x1b[48;5;13m  \x1b[48;5;14m  \x1b[48;5;15m  \x1b[0m\n\nColor cube, 6x6x6:\n\x1b[48;5;16m  \x1b[48;5;17m  \x1b[48;5;18m  \x1b[48;5;19m  \x1b[48;5;20m  \x1b[48;5;21m  \x1b[0m \x1b[48;5;52m  \x1b[48;5;53m  \x1b[48;5;54m  \x1b[48;5;55m  \x1b[48;5;56m  \x1b[48;5;57m  \x1b[0m \x1b[48;5;88m  \x1b[48;5;89m  \x1b[48;5;90m  \x1b[48;5;91m  \x1b[48;5;92m  \x1b[48;5;93m  \x1b[0m \x1b[48;5;124m  \x1b[48;5;125m  \x1b[48;5;126m  \x1b[48;5;127m  \x1b[48;5;128m  \x1b[48;5;129m  \x1b[0m \x1b[48;5;160m  \x1b[48;5;161m  \x1b[48;5;162m  \x1b[48;5;163m  \x1b[48;5;164m  \x1b[48;5;165m  \x1b[0m \x1b[48;5;196m  \x1b[48;5;197m  \x1b[48;5;198m  \x1b[48;5;199m  \x1b[48;5;200m  \x1b[48;5;201m  \x1b[0m \n\x1b[48;5;22m  \x1b[48;5;23m  \x1b[48;5;24m  \x1b[48;5;25m  \x1b[48;5;26m  \x1b[48;5;27m  \x1b[0m \x1b[48;5;58m  \x1b[48;5;59m  \x1b[48;5;60m  \x1b[48;5;61m  \x1b[48;5;62m  \x1b[48;5;63m  \x1b[0m \x1b[48;5;94m  \x1b[48;5;95m  \x1b[48;5;96m  \x1b[48;5;97m  \x1b[48;5;98m  \x1b[48;5;99m  \x1b[0m \x1b[48;5;130m  \x1b[48;5;131m  \x1b[48;5;132m  \x1b[48;5;133m  \x1b[48;5;134m  \x1b[48;5;135m  \x1b[0m \x1b[48;5;166m  \x1b[48;5;167m  \x1b[48;5;168m  \x1b[48;5;169m  \x1b[48;5;170m  \x1b[48;5;171m  \x1b[0m \x1b[48;5;202m  \x1b[48;5;203m  \x1b[48;5;204m  \x1b[48;5;205m  \x1b[48;5;206m  \x1b[48;5;207m  \x1b[0m \n\x1b[48;5;28m  \x1b[48;5;29m  \x1b[48;5;30m  \x1b[48;5;31m  \x1b[48;5;32m  \x1b[48;5;33m  \x1b[0m \x1b[48;5;64m  \x1b[48;5;65m  \x1b[48;5;66m  \x1b[48;5;67m  \x1b[48;5;68m  \x1b[48;5;69m  \x1b[0m \x1b[48;5;100m  \x1b[48;5;101m  \x1b[48;5;102m  \x1b[48;5;103m  \x1b[48;5;104m  \x1b[48;5;105m  \x1b[0m \x1b[48;5;136m  \x1b[48;5;137m  \x1b[48;5;138m  \x1b[48;5;139m  \x1b[48;5;140m  \x1b[48;5;141m  \x1b[0m \x1b[48;5;172m  \x1b[48;5;173m  \x1b[48;5;174m  \x1b[48;5;175m  \x1b[48;5;176m  \x1b[48;5;177m  \x1b[0m \x1b[48;5;208m  \x1b[48;5;209m  \x1b[48;5;210m  \x1b[48;5;211m  \x1b[48;5;212m  \x1b[48;5;213m  \x1b[0m \n\x1b[48;5;34m  \x1b[48;5;35m  \x1b[48;5;36m  \x1b[48;5;37m  \x1b[48;5;38m  \x1b[48;5;39m  \x1b[0m \x1b[48;5;70m  \x1b[48;5;71m  \x1b[48;5;72m  \x1b[48;5;73m  \x1b[48;5;74m  \x1b[48;5;75m  \x1b[0m \x1b[48;5;106m  \x1b[48;5;107m  \x1b[48;5;108m  \x1b[48;5;109m  \x1b[48;5;110m  \x1b[48;5;111m  \x1b[0m \x1b[48;5;142m  \x1b[48;5;143m  \x1b[48;5;144m  \x1b[48;5;145m  \x1b[48;5;146m  \x1b[48;5;147m  \x1b[0m \x1b[48;5;178m  \x1b[48;5;179m  \x1b[48;5;180m  \x1b[48;5;181m  \x1b[48;5;182m  \x1b[48;5;183m  \x1b[0m \x1b[48;5;214m  \x1b[48;5;215m  \x1b[48;5;216m  \x1b[48;5;217m  \x1b[48;5;218m  \x1b[48;5;219m  \x1b[0m \n\x1b[48;5;40m  \x1b[48;5;41m  \x1b[48;5;42m  \x1b[48;5;43m  \x1b[48;5;44m  \x1b[48;5;45m  \x1b[0m \x1b[48;5;76m  \x1b[48;5;77m  \x1b[48;5;78m  \x1b[48;5;79m  \x1b[48;5;80m  \x1b[48;5;81m  \x1b[0m \x1b[48;5;112m  \x1b[48;5;113m  \x1b[48;5;114m  \x1b[48;5;115m  \x1b[48;5;116m  \x1b[48;5;117m  \x1b[0m \x1b[48;5;148m  \x1b[48;5;149m  \x1b[48;5;150m  \x1b[48;5;151m  \x1b[48;5;152m  \x1b[48;5;153m  \x1b[0m \x1b[48;5;184m  \x1b[48;5;185m  \x1b[48;5;186m  \x1b[48;5;187m  \x1b[48;5;188m  \x1b[48;5;189m  \x1b[0m \x1b[48;5;220m  \x1b[48;5;221m  \x1b[48;5;222m  \x1b[48;5;223m  \x1b[48;5;224m  \x1b[48;5;225m  \x1b[0m \n\x1b[48;5;46m  \x1b[48;5;47m  \x1b[48;5;48m  \x1b[48;5;49m  \x1b[48;5;50m  \x1b[48;5;51m  \x1b[0m \x1b[48;5;82m  \x1b[48;5;83m  \x1b[48;5;84m  \x1b[48;5;85m  \x1b[48;5;86m  \x1b[48;5;87m  \x1b[0m \x1b[48;5;118m  \x1b[48;5;119m  \x1b[48;5;120m  \x1b[48;5;121m  \x1b[48;5;122m  \x1b[48;5;123m  \x1b[0m \x1b[48;5;154m  \x1b[48;5;155m  \x1b[48;5;156m  \x1b[48;5;157m  \x1b[48;5;158m  \x1b[48;5;159m  \x1b[0m \x1b[48;5;190m  \x1b[48;5;191m  \x1b[48;5;192m  \x1b[48;5;193m  \x1b[48;5;194m  \x1b[48;5;195m  \x1b[0m \x1b[48;5;226m  \x1b[48;5;227m  \x1b[48;5;228m  \x1b[48;5;229m  \x1b[48;5;230m  \x1b[48;5;231m  \x1b[0m \n\nGrayscale ramp:\n\x1b[48;5;232m  \x1b[48;5;233m  \x1b[48;5;234m  \x1b[48;5;235m  \x1b[48;5;236m  \x1b[48;5;237m  \x1b[48;5;238m  \x1b[48;5;239m  \x1b[48;5;240m  \x1b[48;5;241m  \x1b[48;5;242m  \x1b[48;5;243m  \x1b[48;5;244m  \x1b[48;5;245m  \x1b[48;5;246m  \x1b[48;5;247m  \x1b[48;5;248m  \x1b[48;5;249m  \x1b[48;5;250m  \x1b[48;5;251m  \x1b[48;5;252m  \x1b[48;5;253m  \x1b[48;5;254m  \x1b[48;5;255m  \x1b[0m\n".replace("\n", "\r\n "))
        self.user.Write(sio.getvalue())

    def MenuActionDithering(self):
        self.SetMode(MODE_DEBUG_DISPLAY, "Dithered colour experiment")
        self.UpdateStatusBar(MSG_PRESS_ANY_KEY_TO_RETURN)

        sio = StringIO.StringIO()        
        self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset, sio=sio)
        sio.write(ESC_SCROLL_UP * self.windowHeight)

        sio.write("\r\n")

        sio.write("         ")
        for i, yi in enumerate((40, 42, 44, 46, 40, 42, 44, 46)):
            sio.write("%02d  " % yi)
            if i == 3:
                sio.write(ESC_BOLD)
        sio.write(ESC_RESET_ATTRS)
        sio.write("\r\n")

        sio.write("           ")
        for i, yi in enumerate((41, 43, 45, 47, 41, 43, 45, 47)):
            sio.write("%02d  " % yi)
            if i == 3:
                sio.write(ESC_BOLD)
        sio.write(ESC_RESET_ATTRS)
        sio.write("\r\n")

        for yi in range(8):
            yc = 30 + yi
            sio.write("   %02d  " % yc)
        
            sio.write("\x1b[%dm" % yc)
            sio.write(CHARACTERS("full-block", self.charsetEncoding) + CHARACTERS("full-block", self.charsetEncoding))

            for s in ("", ESC_BOLD):
                for xi in range(8):
                    xc = 40 + xi
                    sio.write("\x1b[%dm" % yc)
                    sio.write("\x1b[%dm" % xc)
                    sio.write(s)
                    sio.write(CHARACTERS("medium-shade", self.charsetEncoding) + CHARACTERS("medium-shade", self.charsetEncoding))
                    sio.write(ESC_RESET_ATTRS)

            sio.write("\r\n")
        self.user.Write(sio.getvalue())

    def MenuActionUnicode(self):
        self.MenuActionCharacters(inUnicode=True)

    def MenuActionCharacters(self, charsetCode=None, inUnicode=False):
        if inUnicode:
            state = "UTF8"
        else:
            state = "CP437"
        self.SetMode(MODE_DEBUG_DISPLAY, "Characters (%s)" % state)

        self.UpdateStatusBar(MSG_PRESS_ANY_KEY_TO_RETURN)

        rowCount = self.windowHeight - 2

        sio = StringIO.StringIO()
        self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset, sio=sio)
        sio.write(ESC_SCROLL_UP * self.windowHeight)

        ranges = []
        if inUnicode:
            firstOrd, lastOrd = 0x2500, 0x257F
            ranges.append((firstOrd, lastOrd))

            firstOrd, lastOrd = 0x25A0, 0x25CF
            ranges.append((firstOrd, lastOrd))

            firstOrd, lastOrd = 0x25D0, 0x25FF
            ranges.append((firstOrd, lastOrd))
            
            firstOrd, lastOrd = 0x2600, 0x267F
            ranges.append((firstOrd, lastOrd))

            firstOrd, lastOrd = 0x2190, 0x21ff
            ranges.append((firstOrd, lastOrd))
            
            sio.write(ESC_UTF8_CHARSET)
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
                    s = eval("u'\\u%x'" % currentOrd).encode("utf8")
                else:
                    c = self.DisplayCharacter(currentOrd, charset=charsetCode)
                    s = "%03d %s" % (currentOrd, c)

                rows[rowOffset % rowCount].append(s)
                rowOffset += 1
                currentOrd += 1
 
        self.MoveCursor(self.windowXStartOffset, self.windowYStartOffset + 1, sio=sio)

        if inUnicode:
            cellWidth = 1
        else:
            cellWidth = len(rows[0][0])
        
        n = self.windowWidth - (cellWidth + 1) * len(rows[0])
        for row in rows:
            rn = n / 2
            ln = n - rn
            sio.write(" " * ln)
            sio.write(" ".join(row))
            if rn > 0:
                sio.write("\r\n")

        if inUnicode:
            sio.write(ESC_DEFAULT_CHARSET)

        self.ResetCharset(sio=sio)
        self.user.Write(sio.getvalue())

    def MenuActionCharsets(self):
        self.SetMode(MODE_DEBUG_DISPLAY, "Character Sets")
        self.UpdateStatusBar(MSG_PRESS_ANY_KEY_TO_RETURN)

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

