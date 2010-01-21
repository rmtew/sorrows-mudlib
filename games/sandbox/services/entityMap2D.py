import stackless
from mudlib import Service
import game.worldMap2D

class Entity2Service(Service):
    __sorrows__ = 'entity2'
    __dependencies__ = set([ 'worldMap2D' ])

    # ==================================================
    # Service

    def Run(self):
        self.entities = []

    def CreateEntity(self):
        entity = game.worldMap2D.Entity(self)
        self.entities.append(entity)
        uthread.new(entity.Run)
