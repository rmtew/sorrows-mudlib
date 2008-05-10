from mudlib.services.intermud3 import Packet

class ChannelListenPacket(Packet):
    __packet_type__ = "channel-listen"
    
    def __init__(self, channelName, flag):
        Packet.__init__(self, mudto=sorrows.i3.routerName)

        self.channelName = channelName
        self.flag = int(flag)

    def List(self):
        l = Packet.List(self)
        l.extend([
            self.channelName,
            self.flag,
        ])
        return l
