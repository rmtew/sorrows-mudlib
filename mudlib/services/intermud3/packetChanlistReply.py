from mudlib.services.intermud3 import Packet

class ChanlistReplyPacket(Packet):
    __packet_type__ = "chanlist-reply"

    def __init__(self, ttl, mudfrom, userfrom, mudto, userto, chanlistID, infoByName):
        Packet.__init__(self, ttl, mudfrom, userfrom, mudto, userto)

        self.chanlistID = chanlistID
        self.infoByName = infoByName

    def List(self):
        raise RuntimeError("Unsupported operation")

#channel_list is mapping with channel names as keys, and an array of two elements as the values. If the value is 0, then the channel has been deleted. The array contains the host mud, and the type of the channel:
#        0  selectively banned
#        1  selectively admitted
#        2  filtered (selectively admitted)

