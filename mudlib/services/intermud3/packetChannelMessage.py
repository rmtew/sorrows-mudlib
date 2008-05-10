from mudlib.services.intermud3 import Packet

class ChannelMessagePacket(Packet):
    __packet_type__ = "channel-m"

    def __init__(self, packetType, ttl, mudfrom, userfrom, mudto, userto, channelName, visName, message):
        Packet.__init__(self, packetType, ttl, mudfrom, userfrom, mudto, userto)

        self.channelName = channelName
        self.visName = visName
        self.message = message

    def List(self):
        raise RuntimeError("Unsupported operation")
