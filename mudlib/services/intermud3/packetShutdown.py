from mudlib.services.intermud3 import Packet

class ShutdownPacket(Packet):
    __packet_type__ = "shutdown"

    def __init__(self, packetType, ttl, mudfrom, userfrom, mudto, userto, restartDelay):
        Packet.__init__(self, packetType, ttl, mudfrom, userfrom, mudto, userto)

        self.restartDelay = restartDelay

    def List(self):
        return Packet.List(self).extend([
            self.restartDelay,
        ])
