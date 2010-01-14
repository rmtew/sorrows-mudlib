import hashlib, random
from base64 import b64decode, b64encode

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
        user = matches[0]
        return user.passwordHash == self.Hash(password, user.passwordSalt)

    def Hash(self, password, salt):
        m = hashlib.sha1()
        m.update(password)
        m.update(salt)
        return m.hexdigest()

    def AddUser(self, userName, password):
        if self.UserExists(userName):
            raise RuntimeError("AddUserExists")

        row = self.table.AddRow()
        row.userName = userName
        row.passwordSalt = "".join(chr(random.randrange(256)) for i in xrange(16))        
        row.passwordHash = self.Hash(password, row.passwordSalt)
        
        return row
