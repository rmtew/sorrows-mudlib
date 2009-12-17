from mudlib.services.net import Connection


class MudConnection(Connection):
    def Setup(self, manager, connID=None):
        Connection.Setup(self, manager, connID)
        self.readBuffer = ''

    def OnDisconnection(self):
        self.service.OnDisconnection(self)

    # -----------------------------------------------------------------------
    #  read
    # -----------------------------------------------------------------------
    def read(self, byteCount):
        while len(self.readBuffer) < byteCount:
            s = self.recv(4096)
            if s == "":
                return ""
            self.readBuffer += s
        ret = self.readBuffer[:byteCount]
        self.readBuffer = self.readBuffer[byteCount:]
        return ret

    # -----------------------------------------------------------------------
    #  ReadPacket
    # -----------------------------------------------------------------------
    def ReadPacket(self):
        # If we do not have a packet length, we're waiting to read one.
        inBuffer = self.read(4)
        if inBuffer == "":
            return None
        # We have a packet length?
        packetSize = 0
        for i in range(4):
            packetSize = packetSize << 8
            c = ord(inBuffer[i])
            packetSize = packetSize + c
        inBuffer = self.read(packetSize)
        if inBuffer == "":
            return None
        # Process the packet into a psuedo LPC structure...
        return MUD2Python(inBuffer)

    # -----------------------------------------------------------------------
    #  SendPacket
    # -----------------------------------------------------------------------
    def SendPacket(self, packet):
        p = Python2MUD(packet.List())
        i = len(p)
        s2 = chr(i % 256)
        i = i >> 8
        s2 = chr(i % 256) + s2
        i = i >> 8
        s2 = chr(i % 256) + s2
        i = i >> 8
        s2 = chr(i % 256) + s2
        self.send(s2 + p)


LPC_NONE = 0
LPC_STRING = 1
LPC_MAPPING = 2
LPC_ARRAY = 3

# -----------------------------------------------------------------------
#  MUD2Python - Convert a saved LPC variable into a python representation.
# -----------------------------------------------------------------------

def MUD2Python(text):
    # If this is a mud-mode packet then it may have trailing null bytes.
    # If its a line from a save_object call, then it won't.
    boundaryOffset = 0
    while text[boundaryOffset-1] == '\0':
        boundaryOffset -= 1
    i = 0
    info = []
    current = None
    key = None
    state = LPC_NONE
    try:
        boundary = len(text) + boundaryOffset
        while i < boundary:
            if state == LPC_ARRAY and text[i] == ',':
                i = i + 1
                if current != None:
                    info[-1][1].append(current)
                    current = None
            elif state == LPC_ARRAY and text[i] == '}' and text[i+1] == ')':
                i = i + 2
                state = info[-1][0]
                current = info[-1][1]
                info = info[0:-1]
            elif state == LPC_MAPPING and text[i] == ':':
                i = i + 1
                if current != None:
                    key = current
                    current = None
            elif state == LPC_MAPPING and text[i] == ',':
                i = i + 1
                if current != None:
                    info[-1][1][key] = current
                    key = None
                    current = None
            elif state == LPC_MAPPING and text[i] == ']' and text[i+1] == ')':
                i = i + 2
                state = info[-1][0]
                current = info[-1][1]
                key = info[-1][2]
                info = info[0:-1]
            elif text[i] == '(' and text[i+1] == '[':
                # The start of a mapping.
                i = i + 2
                info.append((state, {}, key))
                state = LPC_MAPPING
            elif text[i] == '(' and text[i+1] == '{':
                # The start of an array.
                i = i + 2
                info.append((state, []))
                state = LPC_ARRAY
            elif text[i] == '"' or text[i] == "'":
                # The start of a string.
                i = i + 1
                findingEnd = 1
                while findingEnd:
                    j = text.find('"', i)
                    k = j - 1
                    count = 0
                    while text[k] == '\\':
                        count = count + 1
                        k = k - 1
                    # If its an even number, then its a valid end of string.
                    if count % 2 == 0:
                        findingEnd = 0
                s = text[i:j]
                s = s.replace('\"', '"')
                current = s.replace('\\\\', '\\')
                i = j + 1
            else:
                # Its better be an integer or float.
                # Look for a colon otherwise a comma.
                j1 = text.find(':', i)
                j2 = text.find(',', i)
                if j1 != -1 and j2 != -1:
                    j = j1 < j2 and j1 or j2
                elif j2 != -1:
                    j = j2
                else:
                    j = boundary
                s = text[i:j]
                k = text.find('.', i)
                if k == -1 or k > j:
                    current = int(s)
                else:
                    current = float(s)
                i = j
    except Exception:
        print 'ERROR in MUD2Python', i, text[i-5:i] +']]'+ text[i] +'[['+ text[i+1:i+5]
        print "TEXT STARTS"
        print text
        print "TEXT ENDS"
        import traceback
        traceback.print_exc()
    return current

# -----------------------------------------------------------------------
#  Python2MUD - Convert a python representation into a saved LPC variable.
# -----------------------------------------------------------------------

def Python2MUD(mixed):
    """Convert a Python data structure into a saved LPC string."""
    if type(mixed) is list:
        s = '({'
        for value in mixed:
            s += Python2MUD(value) + ','
        s += '})'
    elif type(mixed) is dict:
        s = '(['
        for pair in mixed.iteritems():
            s += Python2MUD(pair[0])
            s += ':'
            s += Python2MUD(pair[1])
            s += ','
        s += '])'
    elif type(mixed) is str:
        s = '"'

        s2 = mixed.replace("\\", "\\\\")
        s2 = s2.replace("\n", "\r")

        s += s2 + '"'
    else:
        s = str(mixed)

    return s
