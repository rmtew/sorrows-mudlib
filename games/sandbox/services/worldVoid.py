# Encapsulate a world.

import os, random, time

from stacklesslib.main import sleep as tasklet_sleep
from mudlib import Service
from game.worldVoid import Body

class WorldVoidService(Service):
    __sorrows__ = 'worldVoid'

    # ==================================================
    # Service

    def Run(self):
        self.bodiesByUsername = {}
        self.objectsByPosition = {}
        self.simulationStartTime = None

    # ==================================================
    # Support

    def AddUser(self, user):
        if self.bodiesByUsername.has_key(user.name):
            raise RuntimeError("User", user.name, "already present")
        body = Body(self, user)
        self.bodiesByUsername[user.name] = body
        user.SetBody(body)
        return body

    def RemoveUser(self, user):
        if not self.bodiesByUsername.has_key(user.name):
            raise RuntimeError("User", user.name, "not present")
        body = self.bodiesByUsername[user.name]
        del self.bodiesByUsername[user.name]
        user.SetBody(None)
        body.Release()

    def GetBody(self, user):
        return self.bodiesByUsername[user.name]

    def PlaceEntity(self, position):
        entity = sorrows.entityVoid.CreateEntity()
        entity.SetPosition(position)
        return entity

    def IsSimulationRunning(self, startTime):
        return self.simulationStartTime == startTime

    # ========================================================================
    # StartSimulation
    # ========================================================================
    def RunSimulation(self, seconds):
        startTime = self.simulationStartTime = time.time()
        print "Simulation: Start", startTime, "period (s)", seconds
        sorrows.entityVoid.StartSimulation(startTime)
        endTime = startTime + seconds
        tasklet_sleep(seconds)
        self.simulationStartTime = None
        print "Simulation: End", endTime, "period (s)", seconds

    # ========================================================================
    # MoveObject - Change the position an object is located at.
    # ========================================================================
    def MoveObject(self, body, offset):
        try:
            position = self.GetOffsetPosition(body.position, offset)
        except:
            raise RuntimeError("MovementFailure", "There seems to be something preventing your movement in that direction.")
        body.SetPosition(position)

    # ========================================================================
    # GetOffsetPosition - Allow for limiting the movement possibilities.
    # ========================================================================
    def GetOffsetPosition(self, position, offset):
        x = position[0] + offset[0]
        y = position[1] + offset[1]
        return x, y

    # ========================================================================
    # OnObjectMoved - Track movement of objects.
    # ========================================================================
    def OnObjectMoved(self, object, newPosition):
        oldPosition = object.position

        if oldPosition is not None:
            # Unindex the object from the old position.
            if self.objectsByPosition.has_key(oldPosition):
                self.objectsByPosition[oldPosition].remove(object)

        if newPosition is not None:
            # Index the object at the new position.
            if not self.objectsByPosition.has_key(newPosition):
                self.objectsByPosition[newPosition] = [ object ]
            else:
                self.objectsByPosition[newPosition].append(object)

    # ========================================================================
    # OnObjectReleased - Clean up after a released object.
    # ========================================================================
    def OnObjectReleased(self, object):
        # Make sure the object is unindexed.
        self.OnObjectMoved(object, None)
