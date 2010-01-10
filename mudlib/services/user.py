import datalayer
from mudlib import Service

class UserService(Service):
    __sorrows__ = 'users'
    __dependencies__ = set([ 'data' ])

    def Run(self):
        self.table = sorrows.data.store.users

    def UserExists(self, userName):
        matches = self.table.Lookup("userName", userName, transform=lambda s: s.lower())
        return len(matches)

    def CheckPassword(self, userName, password):
        matches = self.table.Lookup("userName", userName, transform=lambda s: s.lower())
        return matches[0].password == password

    def AddUser(self, userName, password):
        if self.UserExists(userName):
            raise RuntimeError("AddUserExists")

        row = self.table.AddRow()
        row.userName = userName
        row.password = password
        
        return row
