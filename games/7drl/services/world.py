# Encapsulate a world.

import os, random, time

from mudlib import Service
from game.world import Body
from game.shells import RoguelikeShell

MAP = """
##########
#        #
#   @    #
#        #
#        #
##########
"""



class WorldService(Service):
    __sorrows__ = 'world'

    # ==================================================
    # Service

    def Run(self):
        self.bodiesByUsername = {}


        # CREATE THE WORLD
        if False:
            self.objectsByPosition = {}
            self.simulationStartTime = None

    def OnUserEntersGame(self, user, body):
        body.SetShortDescription(user.name.capitalize())        
        # body.MoveTo(self.startingRoom)

        RoguelikeShell().Setup(user.inputstack)


    def AddUser(self, user):
        if self.bodiesByUsername.has_key(user.name):
            raise RuntimeError("User", user.name, "already present")

        body = Body(self, user)
        self.bodiesByUsername[user.name] = body
        user.SetBody(body)

        self.OnUserEntersGame(user, body)

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
