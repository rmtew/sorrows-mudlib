from mudlib import Command
from mudlib.services.intermud3 import Packet, ChannelMessagePacket

class DynamicChannelCommand(Command):
    def Run(self, verb, arg):
        action = arg.strip().lower()
    
        offProperty = verb +"-off"
        userProperties = self.shell.user.properties

        if action == "off":
            if offProperty in userProperties:
                self.shell.user.Tell("Intermud-3 channel '%s' is already turned off." % verb)
            else:
                self.shell.user.Tell("Intermud-3 channel '%s' turned off." % verb)
                userProperties[offProperty] = None
            return
        elif action == "on":
            if offProperty in userProperties:
                del userProperties[offProperty]
                self.shell.user.Tell("Intermud-3 channel '%s' turned on." % verb)
            else:
                self.shell.user.Tell("Intermud-3 channel '%s' is already turned on." % verb)
            return

        if offProperty in userProperties:
            self.shell.user.Tell("You have the intermud-3 channel '%s' turned off." % verb)
            return

        # Construct the packet.
        userName = self.shell.user.name
        p = ChannelMessagePacket(5, Packet.mudfrom, userName, 0, 0, verb, userName, arg)
        # Send the packet.
        sorrows.i3.connection.SendPacket(p)
