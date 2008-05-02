from mudlib.services.intermud3 import Packet

class StartupPacket(Packet):
    __packet_type__ = "startup-req-3"

    def __init__(self, mudto, password, mudlistID, chanlistID, loginPort, driver, mudlib, mudtype, status, emailAddress):
        Packet.__init__(self, mudto=mudto)

        self.password = password
        self.mudlistID = mudlistID
        self.chanlistID = chanlistID
        self.port = loginPort
        self.port_tcp = 0
        self.port_udp = 0
        self.mudlib = mudlib
        self.baselib = mudlib
        self.driver = driver
        self.mudtype = mudtype
        self.status = status
        self.email = emailAddress
        self.services = { "ucache": 0 }
        self.other = 0

    def List(self):
        l = Packet.List(self)
        l.extend([
            self.password,
            self.mudlistID,
            self.chanlistID,

            self.port,
            self.port_tcp,
            self.port_udp,
            self.mudlib,
            self.baselib,
            self.driver,
            self.mudtype,
            self.status,
            self.email,
            self.services,
            self.other,
        ])
        return l
