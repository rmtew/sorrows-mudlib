from mudlib.services.intermud3 import Packet

class MudlistPacket(Packet):
    __packet_type__ = "mudlist"

    def __init__(self, ttl, mudfrom, userfrom, mudto, userto, mudlistID, infoByName):
        Packet.__init__(self, ttl, mudfrom, userfrom, mudto, userto)

        self.mudlistID = mudlistID
        self.infoByName = infoByName

        # mudName :
#        ({
#            (int)     state,
#            (string)  ip_addr,
#            (int)     player_port,
#            (int)     imud_tcp_port,
#            (int)     imud_udp_port,
#            (string)  mudlib,
#            (string)  base_mudlib,
#            (string)  driver,
#            (string)  mud_type,
#            (string)  open_status,
#            (string)  admin_email,
#            (mapping) services
#            (mapping) other_data
#        })

#Each record of information should replace any prior record for a particular mud. If the mapping's value is zero, then the mud has been deleted (it went down and has not come back for a week) from the Intermud.
#state is an integer with the following values:
#
#        -1  mud is up
#         0  mud is down
#         n  mud will be down for n seconds

    def List(self):
        raise RuntimeError("Unsupported operation")

