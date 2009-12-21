import socket, stackless, uthread

from mudlib import Service
from mudlib.services import intermud3
from mudlib.services.net import MudConnection


class Intermud3Service(Service):
    __sorrows__ = 'i3'
    __dependencies__ = [ 'net' ]
    __optional__ = True

    # -----------------------------------------------------------------------
    # Run - Event indicating the service is being started
    # -----------------------------------------------------------------------
    def Run(self):
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
        
        self.desiredListenChannels = [ "imud_gossip", "discworld-chat" ]

        uthread.new(self.ConnectToRouter)

    # -----------------------------------------------------------------------
    # OnStop - Event indicating the service is being stopped
    # -----------------------------------------------------------------------
    def OnStop(self):
        if self.connection is not None:
            # Notify the router that we are going down.
            self.LogInfo("Sending shutdown packet to router '%s'", sorrows.data.config.intermud3.routername)
            p = intermud3.ShutdownPacket()
            self.connection.SendPacket(p)

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

        self.LogInfo("Connecting to %s %s", config.host, config.getint("port"))
        currentSocket.connect((config.host, config.getint("port")))
        uthread.new(self.ManageConnection)

    # -----------------------------------------------------------------------
    # OnDisconnection - A socket disconnected.
    # -----------------------------------------------------------------------
    def OnDisconnection(self, connection):
        self.LogInfo("Disconnected")
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

        self.LogInfo("Sending the startup packet")
        p = intermud3.StartupPacket(config.routerName, password, mudlistID, chanlistID, int(sorrows.data.config.net.port), identity.driver, identity.mudlib, identity.mudtype, identity.status, identity.email)
        self.connection.SendPacket(p)
        self.LogInfo("Sent the startup packet")

        while True:
            if not self.HandlePacket(config):
                break

        self.LogInfo("Intermud3.ManageConnection.Exit")

    def HandlePacket(self, config):        
        rawPacket = self.connection.ReadPacket()
        if rawPacket is None:
            return False

        packetType = rawPacket[0]

        if self.packetClassesByType.has_key(packetType):
            try:
                packet = self.packetClassesByType[packetType](*rawPacket[1:])
            except Exception:
                self.LogError("BROKEN PACKET %s %s %s", packetType, len(rawPacket), rawPacket[:6])
                import traceback
                traceback.print_exc()
                return True

            if packet.__class__ is intermud3.StartupReplyPacket:
                self.LogInfo("packet %s %s %s", packetType, packet.password, packet.routerList)
                # In the future, use the router name from the reply packet.
                config.routerName, routerAddress = packet.routerList[0]
                host, port = routerAddress.strip().split(" ")
                # In the future, use the router host and port from the reply packet.
                config.host = host
                config.port = int(port)
                # Save the password the router has allocated us.
                config.password = packet.password
                # Store the name of the router we are connected to for use in outgoing packets.
                self.routerName = packet.mudfrom

                # Tell the router we want to listen to specific channels.
                uthread.new(self.SendChannelListenPackets, self.desiredListenChannels)

            elif packet.__class__ is intermud3.MudlistPacket:
                if len(packet.infoByName) < 10:
                    self.LogInfo("packet %s %s %s %s", packetType, packet.mudlistID, len(packet.infoByName), packet.infoByName.keys())
                else:
                    self.LogInfo("packet %s %s %s", packetType, packet.mudlistID, len(packet.infoByName))

                config.mudlistID = packet.mudlistID
                self.mudInfoByName.update(packet.infoByName)

            elif packet.__class__ is intermud3.ChanlistReplyPacket:
                config.chanlistID = packet.chanlistID
                self.channelInfoByName.update(packet.infoByName)
                self.LogInfo("channel list %s", packet.infoByName.keys())

            elif packet.__packet_type__.endswith("-req"):
                self.LogInfo(packet.LogEntry())

                if packet.__reply_type__ not in self.packetClassesByType:
                    self.LogError("Unable to find reply packet class %s", packet.__reply_type__)
                    return True

                replyPacket = self.packetClassesByType[packet.__reply_type__]()
                replyPacket.ProcessRequestPacket(packet)
                self.connection.SendPacket(replyPacket)

            else:
                self.LogInfo(packet.LogEntry())

                packet.ProcessPayload()

        else:
            self.LogWarning("Packet unrecognised %s", rawPacket)

        return True

    # =======================================================================

    # -----------------------------------------------------------------------
    def SendChannelListenPackets(self, channelList):
        for channelName in channelList:
            self.LogInfo("Sending channel listen packet for '%s'", channelName)
            p = intermud3.ChannelListenPacket(channelName, True)
            self.connection.SendPacket(p)
            
            self.LogInfo("Registering dynamic channel command: %s", channelName)
            sorrows.commands.RegisterDynamicCommand(channelName, intermud3.DynamicChannelCommand)

