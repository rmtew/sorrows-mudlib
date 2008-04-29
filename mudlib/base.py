



class Group:
    def __init__(self):
        self.members = {}
    def AddMember(self,memberID,member):
        self.members[memberID] = member
    def RemoveMember(self,memberID):
        del self.members[memberID]
    def Tell(self,message):
        msg = message+'\r\n'
        for member in self.members.values():
            member.send(msg)
#        map(self.members.values(),msg)



