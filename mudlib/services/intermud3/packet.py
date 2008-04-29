
class Packet:
    __packet_type__ = "EMPTY"
    mudfrom = 'MisconfiguredMud'

    def __init__(self, packetType=None, ttl=5, mudfrom=None, userfrom=0, mudto=0, userto=0):
        if packetType is None:
            self.packetType = self.__packet_type__
        else:
            self.packetType = packetType
        self.ttl = ttl
        if mudfrom is not None:
            self.mudfrom = mudfrom
        self.userfrom = userfrom
        self.mudto = mudto
        self.userto = userto

    def List(self):
        return [
            self.packetType,
            self.ttl,
            self.mudfrom,
            self.userfrom,
            self.mudto,
            self.userto
        ]
