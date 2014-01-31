class Container(object):
    def __init__(self):
        super(Container, self).__init__()
        self.contents = []

    def AddObject(self, ob):
        self.contents.append(ob)

    def RemoveObject(self, ob):
        self.contents.remove(ob)

    def GetContainedWeight(self):
        weight = 0.0
        for ob in self.contents:
            weight += ob.GetTotalWeight()
        return weight

    def GetTotalWeight(self):
        return self.weight + self.GetContainedWeight()
