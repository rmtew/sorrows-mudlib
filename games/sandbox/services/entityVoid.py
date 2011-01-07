import stackless
from mudlib import Service
from game.worldVoid import Entity

class EntityVoidService(Service):
    __sorrows__ = 'entityVoid'
    __dependencies__ = set([ 'worldVoid' ])

    # ==================================================
    # Service

    def Run(self):
        self.entities = []

    def CreateEntity(self):
        entity = Entity()
        self.entities.append(entity)
        return entity

    def StartSimulation(self, startTime):
        for entity in self.entities:
            stackless.tasklet(entity.Run, startTime)()

    def EndSimulation(self, startTime):
        for entity in self.entities:
            pass
