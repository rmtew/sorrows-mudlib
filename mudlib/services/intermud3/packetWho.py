from mudlib.services.intermud3 import RequestPacket, ReplyPacket


class WhoRequestPacket(RequestPacket):
    __packet_type__ = "who-req"
    __reply_type__ = "who-reply"

    def LogEntry(self):
        return "Who request from %s@%s" % (self.userfrom, self.mudfrom)

    def List(self):
        raise RuntimeError("Unsupported operation")


class WhoReplyPacket(ReplyPacket):
    __packet_type__ = "who-reply"
    
    def PreparePayload(self, request):
        l = []
        for conn in sorrows.net.telnetConnections:
            l.append([
                conn.user.name,
                66,
                "Don't trust the idle time",
            ])
        self.whoData = l

    def Payload(self):
        return [ self.whoData ]
