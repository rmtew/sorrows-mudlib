from mudlib.services.intermud3 import Packet

class StartupReplyPacket(Packet):
    __packet_type__ = "startup-reply"

    def __init__(self, ttl, mudfrom, userfrom, mudto, userto, routerList, password):
        Packet.__init__(self, ttl, mudfrom, userfrom, mudto, userto)

        self.routerList = routerList
        self.password = password

    def List(self):
        raise RuntimeError("Unsupported operation")
