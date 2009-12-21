
class Packet:
    __packet_type__ = "EMPTY"

    # This is set by the intermud3 service to the correct value.
    mudfrom = 'MisconfiguredMud'

    def __init__(self, ttl=5, mudfrom=None, userfrom=0, mudto=0, userto=0):
        self.ttl = ttl
        if mudfrom is not None:
            self.mudfrom = mudfrom
        self.userfrom = userfrom
        self.mudto = mudto
        self.userto = userto

    def List(self):
        ret = [
            self.__packet_type__,
            self.ttl,
            self.mudfrom,
            self.userfrom,
            self.mudto,
            self.userto,
        ]
        ret.extend(self.Payload())
        return ret

    def Payload(self):
        return []


class MessagePacket(Packet):
    def LogEntry(self):
        return [ "%s", Packet.List(self) ]

    def ProcessPayload(self):
        pass

    def List(self):
        raise Exception("Unsupported operation")


class RequestPacket(MessagePacket):
    __reply_type__ = None


class ReplyPacket(Packet):
    def ProcessRequestPacket(self, request):
        self.ttl = request.ttl
        # mudfrom defaults to our MUD name.
        # userto defaults to 0.
        self.mudto = request.mudfrom
        self.userto = request.userfrom

        self.PreparePayload(request)

    def PreparePayload(self, request):
        pass

    def List(self):
        ret = Packet.List(self)
        print "REPLY", ret
        return ret
