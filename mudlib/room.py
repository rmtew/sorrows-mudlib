from mudlib import Group

class Room(Group):
    def __init__(self):
        Group.__init__(self)
        self.players = []

    def OnEnter(self,player, reason = "%s enters."):
        self.Tell(reason%player.name)
        self.AddMember(player.connectionID, player.connection)
        if player not in self.players:
            self.players.append(player)


    def OnLeave(self,player,reason = "%s leaves."):
        self.RemoveMember(player.connectionID)
        if player in self.players:
            self.players.remove(player)
        #uthread.Sleep(2)
        self.Tell(reason%player.name)

    def PlayerExists(self, mname):
        mname = mname.lower()
        for user in self.players:
            if user.name.lower() == mname:
                return 1
        return 0

    def Tell(self, message, exclude=None):
        msg = message+'\r\n'
        [member.Tell(msg) for member in self.players if member is not exclude]
            
            
