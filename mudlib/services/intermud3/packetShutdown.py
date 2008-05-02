from mudlib.services.intermud3 import Packet

class ShutdownPacket(Packet):
    __packet_type__ = "shutdown"
    
    # restartDelay:
    # 0: Unknown

    def __init__(self, restartDelay=0):
        Packet.__init__(self)

        self.restartDelay = restartDelay

    def List(self):
        return Packet.List(self).extend([
            self.restartDelay,
        ])
