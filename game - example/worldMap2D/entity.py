import uthread

class Entity:
    def __init__(self, service):
        self.service = service

    def Run(self):
        # Place an entity.
        #  Ask the world service to allocate one of the free house squares.
        #  Ask the world service to find a field square.
        #  At sunrise, have the entity head out to the field.
        #  At mid-afternoon, have the entity head back home.
        #    That requires some sort of time service.
        while self.service.IsRunning():
            uthread.Sleep(10)
