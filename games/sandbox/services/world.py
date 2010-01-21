# Work in progress.
#
# Can only have one terrain.

import math, random, weakref, stackless
from mudlib import Service

class WorldService(Service):
    __sorrows__ = 'world'
    __dependencies__ = set([ 'data' ])

    def Run(self):
        self.example = Planet(9235632, 6378000.0, 10000.0, 0.15)
        return
        spherical = False
        import renderer
        #spherical = True#False
        def getV(x,y):
            y = (y-90)/180.0 * math.pi
            x = x/180.0 * math.pi
            #print y,x
            vec = math.sin(y)*math.cos(x), math.sin(y)*math.sin(x), math.cos(y)
            sorrows.terrain.SetSeed(self.example.seed)

            height = sorrows.terrain.fBm(8, *vec)
            if height > 0.4:
                color = 1,1,1
            elif height < 0:
                color = 0,0.2*(1.0+height),0.5+abs(height)/2
                height = 0.0
            else:
                color = 0,height,0
            if not spherical:
                return (x,y,height)+color # uncomment for 2d representation
            height =  1 + height*0.2

            return (vec[0] *height, vec[1]*height, vec[2] * height) + color
#            return x,y,self.example.GetSurfaceHeight(vec)-self.example.radius
        uthread.new(renderer.Render, getV)


# Planet representation..
#

class Planet:
    def __init__(self, seed, radius, variance, seaRatio):
        self.seed = seed

        # Average distance from the center of the planet to the surface.
        self.radius = radius
        # Distance around the planet.
        self.circumference = 2 * math.pi * radius
        # Radians for 1 meter surface distance.
        self.meterRadians = (2 * math.pi) / radius
        # Variance in surface distance.  Both up and down.
        self.variance = variance

        self.seaRatio = seaRatio
        # Distance from the center of the planet to sea level.
        self.seaLevel = radius + variance * seaRatio

    # ------------------------------------------------------------------------
    #  GetSurfaceHeight
    # ------------------------------------------------------------------------
    # If the height is less than the sea level then its underwater.
    # If the height is greater than the sea level then its above water.
    # ------------------------------------------------------------------------
    def GetSurfaceHeight(self, *pos):
        if len(pos) == 1:
            pos = pos[0]
        if not isinstance(pos, Vector):
            pos = Vector(pos)
        x, y, z = pos.NormalisedTuple()
        # Maybe I should pass the seed in the fBm call.
        sorrows.terrain.SetSeed(self.seed)
        return self.radius + sorrows.terrain.fBm(8, x, y, z) * self.variance

    def GetRandomSurfacePosition(self):
        v = Vector(random.random(), random.random(), random.random())
        height = self.GetSurfaceHeight(v)
        v.Normalise()
        return PlanetaryPosition(self, v, height)


class Vector:
    def __init__(self, *args):
        if len(args) == 1:
            x, y, z = args[0]
        elif len(args) == 3:
            x, y, z = args
        self.x = x
        self.y = y
        self.z = z

    def Length(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def Normalise(self):
        self.x, self.y, self.z = self.NormalisedTuple()
        return self

    def Normalised(self):
        return Vector(self.NormalisedTuple())

    def NormalisedList(self):
        length = self.Length()
        return [ self.x/length, self.y/length, self.z/length ]

    def NormalisedTuple(self):
        length = self.Length()
        return self.x/length, self.y/length, self.z/length


# PlanetaryPosition
#
# Represents the position of an object from a planets center.

class PlanetaryPosition:
    def __init__(self, planet, vector, distance):
        self.planet = weakref.ref(planet)

        # Should be normalised.
        self.vector = vector
        self.distance = distance


class Thing:
    def SetPosition(self, position):
        self.position = position

    def Move(self, compassDirection, distance=1):
        # rotate up is north
        # rotate down is south
        # rotate counter-clockwise around globe is east
        # rotate clockwise around globe is west
        # x axi
        pass
