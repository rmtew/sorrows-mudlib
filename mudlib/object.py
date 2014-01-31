class Object(object):
    weight = 0.0

    def SetWeight(self, weight):
        self.weight = weight

    def GetContainedWeight(self):
        return 0.0
    
    def GetTotalWeight(self):
        return self.weight

    def Release(self):
        pass
