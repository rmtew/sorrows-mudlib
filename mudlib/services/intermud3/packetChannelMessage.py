from mudlib.services.intermud3 import MessagePacket

class ChannelMessagePacket(MessagePacket):
    __packet_type__ = "channel-m"

    def __init__(self, ttl, mudfrom, userfrom, mudto, userto, channelName, visName, message):
        Packet.__init__(self, ttl, mudfrom, userfrom, mudto, userto)

        self.channelName = channelName
        self.visName = visName
        self.message = message

    def ProcessPayload(self):
        s = "[%s] %s@%s: %s" % (self.channelName, self.userfrom, self.mudfrom, self.message)
        for conn in sorrows.net.telnetConnections:
            conn.user.Tell(s)
