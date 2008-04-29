from mudlib import Object

class Body(Object):
    def __init__(self, service, user):
        Object.__init__(self, service)

        self.service = service
        self.user = user

    def Release(self):
        Object.Release(self)
