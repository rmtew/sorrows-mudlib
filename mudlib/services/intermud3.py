import socket, stackless, uthread

from mudlib import Service
from mudlib.services import intermud3
from mudlib.services.net import MudConnection


class Intermud3Service(Service):
    __sorrows__ = 'i3'
    __dependencies__ = [ 'net' ]
    __optional__ = 1

    # -----------------------------------------------------------------------
    # Run - Event indicating the service is being started
    # -----------------------------------------------------------------------
    def Run(self):
        self.tablesSavePath = sorrows.services.gameDataPath +"tables.db"

        # Locate all the packet classes and index them by their official packet name.
        packetClassesByType = {}
        for each in dir(intermud3):
            # Collect every class ending in "Packet" except the base class.
            if each == "Packet" or not each.endswith("Packet"):
                continue
            klass = getattr(intermud3, each)
            packetClassesByType[klass.__packet_type__] = klass
        self.packetClassesByType = packetClassesByType

        # Chanlist data.
        self.mudInfoByName = {}
        self.channelInfoByName = {}

        uthread.new(self.ConnectToRouter)

    # -----------------------------------------------------------------------
    # OnStop - Event indicating the service is being stopped
    # -----------------------------------------------------------------------
    def OnStop(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    # -----------------------------------------------------------------------
    # ConnectToRouter
    # -----------------------------------------------------------------------
    def ConnectToRouter(self):
        currentSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = MudConnection(currentSocket)
        self.connection.Setup(self)
        config = sorrows.data.config.intermud3
        print "Service intermud3: Connecting to", config.host, config.getint("port")
        currentSocket.connect((config.host, config.getint("port")))
        uthread.new(self.ManageConnection)

    # -----------------------------------------------------------------------
    # OnDisconnection - A socket disconnected.
    # -----------------------------------------------------------------------
    def OnDisconnection(self, connection):
        print "Intermud disconnection"
        self.connection.Release()
        self.connection = None

    # -----------------------------------------------------------------------
    # ManageConnection
    # -----------------------------------------------------------------------
    def ManageConnection(self):
        identity = sorrows.data.config.identity
        intermud3.Packet.mudfrom = identity.name

        config = sorrows.data.config.intermud3

        password = config.getint("password", 0)
        mudlistID = config.getint("mudlistID", 0)
        chanlistID = config.getint("chanlistID", 0)

        p = intermud3.StartupPacket(config.routerName, password, mudlistID, chanlistID, identity.driver, identity.mudlib, identity.mudtype, identity.status, identity.email)
        self.connection.SendPacket(p)
        while True:
            rawPacket = self.connection.ReadPacket()
            if rawPacket is None:
                break
            packetType = rawPacket[0]

            if self.packetClassesByType.has_key(packetType):
                try:
                    print "i3-packet", packetType
                    packet = self.packetClassesByType[packetType](*rawPacket)
                except:
                    print "BROKEN PACKET", packetType, len(rawPacket), rawPacket[:6]
                    continue

                if packet.__class__ is intermud3.StartupReplyPacket:
                    print "i3-packet", packet.__class__, packet.password, packet.routerList
                    config.routerName, routerAddress = packet.routerList[0]
                    host, port = routerAddress.strip().split(" ")
                    config.host = host
                    config.port = int(port)
                    config.password = packet.password
                elif packet.__class__ is intermud3.MudlistPacket:
                    print "i3-packet", packet.__class__, packet.mudlistID, len(packet.infoByName)
                    config.mudlistID = packet.mudlistID
                    self.mudInfoByName.update(packet.infoByName)
                elif packet.__class__ is intermud3.ChanlistReplyPacket:
                    print "i3-packet", packet.__class__, packet.chanlistID, len(packet.infoByName)
                    config.chanlistID = packet.chanlistID
                    self.channelInfoByName.update(packet.infoByName)
                else:
                    print "i3-packet-raw", rawPacket
            else:
                print "UNRECOGNISED PACKET", rawPacket
        print "Intermud3.ManageConnection.Exit"

    # =======================================================================

    # -----------------------------------------------------------------------
    # Something
    # -----------------------------------------------------------------------
    def Something(self):
        pass
