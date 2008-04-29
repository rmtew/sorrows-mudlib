class Object:
    position = None
    def __init__(self, service):
        self.service = service

    def Release(self):
        self.service.OnObjectReleased(self)
        self.__dict__.clear()

    # ------------------------------------------------------------------------
    # SetPosition
    # ------------------------------------------------------------------------
    def SetPosition(self, position):
        self.service.OnObjectMoved(self, position)
        self.position = position
