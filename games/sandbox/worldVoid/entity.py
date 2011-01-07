# processing action has to take an amount of time.
# movement action has to take an amount of time.

from stacklesslib.main import sleep as tasklet_sleep
import math
import game

class Entity(game.Object):
    def __init__(self):
        game.Object.__init__(self, sorrows.worldVoid)

        self.profession = None
        self.goals = {}
        self.inventory = {}

    def __str__(self):
        return self.profession or "profession-less entity"

    def SetProfession(self, profession):
        self.profession = profession
        # Save the current position as the home location.
        self.homePosition = self.position

        if self.profession == 'farmer':
            self.inventory["grain"] = 0
            self.inventory["bread"] = 1
            self.InitialiseGoal("harvest-grain")
        elif self.profession == 'miller':
            self.inventory["grain"] = 0
            self.inventory["flour"] = 1
            self.inventory["bread"] = 0
            self.InitialiseGoal("sell-flour")
        elif self.profession == 'baker':
            self.inventory["flour"] = 0
            self.inventory["bread"] = 1

    def Run(self, startTime):
        while sorrows.worldVoid.IsSimulationRunning(startTime):
            sleepDelay = 5.0
            if self.profession == 'farmer':
                if self.goals.has_key("sell-grain"):
                    if self.inventory["grain"] == 1:
                        millers = self.FindEntitiesByProfession("miller")
                        if len(millers):
                            miller = millers[0]
                            if not self.ApproachPosition(miller.homePosition):
                                # Reached the miller's home.  Is it present?
                                if miller in sorrows.worldVoid.objectsByPosition[self.position]:
                                    if miller.inventory["bread"] > 0:
                                        self.Debug("sell-grain - miller found / sale")

                                        miller.inventory["bread"] -= 1
                                        miller.inventory["grain"] += 1
                                        self.inventory["bread"] += 1
                                        self.inventory["grain"] -= 1

                                        self.GoalCompleted("sell-grain")
                                        self.InitialiseGoal("harvest-grain")
                                    else:
                                        self.Debug("sell-grain - miller found / wait bread")
                                else:
                                    self.Debug("sell-grain - miller not present")
                        else:
                            self.Debug("sell-grain - no miller exists")
                            break
                    else:
                        self.Debug("sell-grain - no grain")
                        break
                elif self.goals.has_key("harvest-grain"):
                    # If distant from field, approach field.
                    if not self.ApproachPosition(self.homePosition):
                        # Start harvesting process.  Or end it.
                        if self.inventory["grain"] == 0:
                            self.inventory["grain"] += 1
                            self.inventory["bread"] -= 1
                            self.Debug("harvest-grain - harvested")
                        else:
                            self.GoalCompleted("harvest-grain")
                            self.InitialiseGoal("sell-grain")
                elif len(self.goals):
                    self.Debug("bad goals", self.goals)
                    break
            elif self.profession == 'miller':
                if self.goals.has_key("sell-flour"):
                    if self.inventory["flour"] == 1:
                        buyers = self.FindEntitiesByProfession("baker")
                        if len(buyers):
                            buyer = buyers[0]
                            if not self.ApproachPosition(buyer.homePosition):
                                # Reached the buyer's home.  Is it present?
                                if buyer in sorrows.worldVoid.objectsByPosition[self.position]:
                                    if buyer.inventory["bread"] > 0:
                                        self.Debug("sell-flour - baker found / sale")

                                        buyer.inventory["bread"] -= 1
                                        buyer.inventory["flour"] += 1
                                        self.inventory["flour"] -= 1
                                        self.inventory["bread"] += 1

                                        self.GoalCompleted("sell-flour")
                                        self.InitialiseGoal("work")
                                    else:
                                        self.Debug("sell-grain - baker found / wait bread")
                                else:
                                    self.Debug("sell-grain - miller not present")
                    else:
                        self.Debug("sell-flour - no flour")
                        break
                elif self.goals.has_key("work"):
                    # If distant from field, approach field.
                    if not self.ApproachPosition(self.homePosition):
                        grainCount = self.inventory["grain"]
                        if grainCount > 0:
                            self.inventory["grain"] -= grainCount
                            self.inventory["flour"] += grainCount

                            self.GoalCompleted("work")
                            self.InitialiseGoal("sell-flour")
                        else:
                            self.Debug("work - no grain to grind")
                elif len(self.goals):
                    self.Debug("bad goals", self.goals)
                    break
            elif self.profession == 'baker':
                flourCount = self.inventory["flour"]
                if flourCount > 0:
                    self.inventory["flour"] -= flourCount
                    self.inventory["bread"] += flourCount
                    self.Debug("bake", flourCount, "bread")
                else:
                    self.Debug("wait for customer")
            tasklet_sleep(sleepDelay)
        self.Debug("done")

    def FindEntitiesByProfession(self, profession):
        return [
            entity
            for entity in sorrows.entityVoid.entities
            if profession == entity.profession
        ]

    def Debug(self, *args):
        print "Simulation:", (id(self), self.profession), "-", args

    def InitialiseGoal(self, goalName):
        self.goals[goalName] = None
        self.Debug("InitialiseGoal", goalName)

    def GoalCompleted(self, goalName):
        del self.goals[goalName]
        self.Debug("GoalCompleted", goalName)

    # If still approaching, return True.
    # Otherwise, return False.

    def ApproachPosition(self, position):
        direction = [ position[0] - self.position[0], position[1] - self.position[1] ]
        lengthBefore = math.sqrt(direction[0]**2 + direction[1]**2)
        if lengthBefore == 0:
            return False
        offset = [ 0, 0 ]
        for i in range(len(direction)):
            v = direction[i]
            if v != 0:
                # Obtain the sign and reverse it.
                step = v / abs(v)
                offset[i] = step
        sorrows.worldVoid.MoveObject(self, offset)
        direction = [ position[0] - self.position[0], position[1] - self.position[1] ]
        lengthAfter = math.sqrt(direction[0]**2 + direction[1]**2)

        self.Debug("ApproachPosition", (lengthBefore, lengthAfter), direction)

        return True


