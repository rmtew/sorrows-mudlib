import hashlib, random
from base64 import b64decode, b64encode

import datalayer
from mudlib import Service

class UserService(Service):
    __sorrows__ = 'users'
    __dependencies__ = set([ 'data' ])

    def Run(self):
        self.table = sorrows.data.store.users

    def Add(self, userName, password):
        # Constraint: Only one user can exist with the same name.
        if self.UserExists(userName):
            raise RuntimeError("AddUserExists")

        row = self.table.AddRow()
        row.userName = userName
        row.passwordSalt = "".join(chr(random.randrange(256)) for i in xrange(16))        
        row.passwordHash = self.Hash(password, row.passwordSalt)
        
        return row

    def Get(self, userName):
        matches = self.table.Lookup("userName", userName, transform=lambda s: s.lower())
        if len(matches):
            if len(matches) > 1:
                self.LogError("Found more than one user by the name 'userName'", userName)
            return matches[0]

    def UserExists(self, userName):
        return self.Get(userName) is not None

    def CheckPassword(self, userName, password):
        user = self.Get(userName)
        return user.passwordHash == self.Hash(password, user.passwordSalt)

    def Hash(self, password, salt):
        m = hashlib.sha1()
        m.update(password)
        m.update(salt)
        return m.hexdigest()
