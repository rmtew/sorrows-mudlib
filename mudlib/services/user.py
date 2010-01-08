from mudlib import Service

class UserService(Service):
    __sorrows__ = 'users'
    __dependencies__ = set([ 'data' ])

    def Run(self):
        if sorrows.data.TableExists("users"):
            self.table = sorrows.data.GetTable("users")
        else:
            self.table = sorrows.data.AddTable("users", [ "userID", "userName", "password" ])
            self.table.SetIdColumn("userID")

    def UserExists(self, userName):
        row = self.table.FindMatchingRow("userName", userName, caseInsensitive=1)
        return row is not None

    def CheckPassword(self, userName, password):
        row = self.table.FindMatchingRow("userName", userName, caseInsensitive=1)
        idx = self.table.header.index("password")
        return password == row[idx]

    def AddUser(self, userName, password):
        if self.UserExists(userName):
            raise RuntimeError("AddUserExists")
        return self.table.AddRow((userName, password))
