from game.world import Container

GENDER_SHE    = 0
GENDER_HE     = 1
GENDER_NEUTER = 2

class Body(Container):
    gender = GENDER_HE
    verbWord = "carry"
    carriedWeightMax = 12.0

    def __init__(self, service, user):
        super(Body, self).__init__()

        self.service = service
        self.user = user

    def LookString(self, viewer):
        s = super(Body, self).LookString(viewer)
        carriedWeight = self.GetContainedWeight()
        percentage = (self.GetContainedWeight() / self.carriedWeightMax) * 100
        s += "\r\nEncumbrance: %0.1f/%0.1f kg (%d%%)" % (carriedWeight, self.carriedWeightMax, percentage)
        return s

    def GetPronoun(self):
        return [ "she", "he", "it" ][self.gender]

    def GetMaxCarriedWeight(self):
        return self.carriedWeightMax

    def MoveDirection(self, verb):
        destinationRoom = self.container.GetExitRoom(verb)
        if destinationRoom:    
            return self.MoveTo(destinationRoom)

