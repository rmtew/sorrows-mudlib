# octreeExpanding.py
#
# Author: Richard Tew <richard.m.tew@gmail.com>
# Date:   16th October 2008
#

"""
An octree implementation which starts at the smallest size and expands
as it needs to, to encompass the information added to it.

>>> value = 10
>>> tree = Octree()
>>> tree.insert((1,2,3), value)
>>> print tree.lookup((1,2,3))
10
"""

__all__ = [ "Octant", "calc_octant_index", "BASE_SIZE", "DEBUG" ]

DEBUG = True

BASE_SIZE = 64000


def calc_octant_index(vec1, vec2):
    '''
    Given a position and a locus, determine which octant around the locus
    the position falls into, as an index into a suboctant array.
    '''
    bits = 0
    for i in range(3):
        if (vec2[i] - vec1[i]) >= 0:
            bits |= 1 << i
    return bits


class Octree:
    '''
    An octree implementation which starts with the smallest subdivision
    and expands the tree to encompass the area in which additional
    locations lie.
    '''

    def __init__(self):
        '''
        Initialise the octree to be the smallest possible size.
        '''

        if DEBUG:
            # State to support detection of whether we are out of control.
            self.outer_calls = 0
            self.max_outer_calls = 10

        # The initial region covers (0, 0, 0) to (63999, 63999, 63999)
        self.octree = Octant(self, size=64000, pos0=(0, 0, 0))

    def get_outer_octant(self, innerOctant, pos, idxs):
        '''
        A call to this method indicates the need for access to a position
        which is outside the bounds of the current octree.  The octree
        will be expanded, making the calling octant which was previously
        defining the bounds an 'in situ' occupant of the enlargened
        bounds.
        '''

        if DEBUG:
            # Detect if we are out of control / broken.
            self.outer_calls += 1
            if self.outer_calls > self.max_outer_calls:
                raise RuntimeError("Too deep")

        # An octant is divided into eight more suboctants, down to the
        # lowest level.  A new larger octant will have the calling
        # octant as one of its suboctants.  Therefore the new larger
        # octant will be twice the size of the original inner one.
        outerSize = innerOctant.size * 2

        # In order to work our way towards the position that is
        # driving this expansion, we need to expand in its
        # direction.  This way, eventually we will expand to
        # encompass the given position.
        outerPos0 = []
        for i, offset in enumerate(innerOctant.pos0):
            sign = idxs[i]
            if sign < 0:
                # Extend in the negative direction one octant
                # meaning we keep the child octant within us.
                outerPos0.append(offset + sign * innerOctant.size)
            else:
                # We naturally extend in the positive direction
                # by having double the size of the child octant,
                # so we can just share this axis' base offset.
                outerPos0.append(offset)

        # Make the expanded octant and place the calling inner
        # octant within it at the correct location.
        outerOctant = Octant(self, outerSize, tuple(outerPos0))
        outerOctant.insert_existing_octant(innerOctant)
        # The expanded octant is now the outermost one and as
        # such it is representative of the tree.  Make it the
        # tree in effect.
        self.octree = outerOctant

        return outerOctant
        
    def __getattr__(self, attrName):
        '''
        Pretend we are the outermost octant.
        '''

        return getattr(self.octree, attrName)

class Octant:
    '''
    An octree level of subdivision.
    '''

    def __init__(self, parent, size=None, pos0=None):
        self.parent = parent

        # How large in units this octant is.    
        self.size = size
        # The position of the corner of this octant.
        self.pos0 = pos0
        # The center position of this octant.
        self.posC = (pos0[0] + size/2, pos0[1] + size/2, pos0[2] + size/2)

        # The sub-octants of this octant.        
        self.octants = None
        # The occupants of this octant.  There will only be occupants
        # at the lowest level.  The higher levels are just for optimally
        # locating the correct lowest level.
        self.values = None

    def insert(self, pos, value):
        '''
        Insert an occupant within this octant.  It will end up in the octant
        at the lowest level, whether that is this one or one of its children.
        '''
    
        octant = self.__lookup_octant(pos, create=True)
        octant.__insert_value(pos, value)

    def __insert_value(self, pos, value):
        # Initialise the occupants store, if need be.
        if self.values is None:
            self.values = {}

        xValue = pos[0] - self.pos0[0]
        if xValue < 0 or xValue >= BASE_SIZE: raise RuntimeError("Bad x value", xValue)
        if xValue not in self.values:
            self.values[xValue] = {}

        yValue = pos[1] - self.pos0[1]
        if yValue < 0 or yValue >= BASE_SIZE: raise RuntimeError("Bad y value", yValue)
        if yValue not in self.values[xValue]:
            self.values[xValue][yValue] = {}

        zValue = pos[2] - self.pos0[2]
        if zValue < 0 or zValue >= BASE_SIZE: raise RuntimeError("Bad z value", zValue)

        self.values[xValue][yValue][zValue] = value        

    def __get_value(self, pos):
        xValue = pos[0] - self.pos0[0]
        if xValue not in self.values:
            raise KeyError(xValue)

        yValue = pos[1] - self.pos0[1]
        if yValue not in self.values[xValue]:
            raise KeyError(yValue)

        zValue = pos[2] - self.pos0[2]
        return self.values[xValue][yValue][zValue]

    def insert_existing_octant(self, octant):
        '''
        Install a pre-existing suboctant in the correct location.
        '''
    
        # Initialise the sub-octant array, if need be.
        if self.octants is None:
            self.octants = [ None for i in range(8) ]

        # Validate that this octant is a sub-octant of ours.
        for i, offset in enumerate(octant.pos0):
            if offset < self.pos0[i] or offset >= self.pos0[i] + self.size:
                raise RuntimeError("Bad sub-octant")

        # Install the suboctant in the correct location.
        idx = calc_octant_index(self.posC, octant.posC)
        self.octants[idx] = octant

    def lookup(self, pos):
        '''
        If the given position is indexed, return the indexed value.  This is
        done without expanding the octree.
        '''
        octant = self.__lookup_octant(pos, create=False)
        return octant.__get_value(pos)

    def __lookup_octant(self, pos, create=False):
        # Detect if the position is outside the this area, and if so, how.
        axisDirections = []
        for i, offset in enumerate(pos):
            # If this is the case, we want to know the axis and the
            # direction we need to expand (i and sign respectively).
            sign = 0
            if offset < self.pos0[i]:
                sign = -1
            elif offset >= self.pos0[i] + self.size:
                sign = 1
            axisDirections.append(sign)

        # If there is a direction for a given access, then the position is
        # outside of this octant in that direction.
        if axisDirections != [0,0,0]:
            if create:        
                outerOctant = self.parent.get_outer_octant(self, pos, axisDirections)
                return outerOctant.__lookup_octant(pos, create=create)
            raise KeyError(pos)

        # If we are not the smallest size, then we need to go a level deeper.
        if self.size != BASE_SIZE:
            idx = calc_octant_index(self.posC, pos)
            
            octant = None
            if self.octants is None:
                if not create:
                    raise KeyError(pos)
                self.octants = [ None for i in range(8) ]
            elif self.octants[idx] is None:
                if not create:
                    raise KeyError(pos)
            else:
                octant = self.octants[idx]

            if octant is None:
                innerSize = self.size / 2
                # We need to work out where the outer corner of the sub-octant
                # the position falls into is, so we can create it properly.  Our
                # octant index is a reverse bit field of axis sign, so we can
                # use that to help us.            
                innerPos0 = list(self.pos0)
                for i in range(3):
                    if idx & (1 << i):
                        innerPos0[i] += innerSize
                octant = self.octants[idx] = Octant(self, innerSize, tuple(innerPos0))

            return octant.__lookup_octant(pos, create=create)

        return self

if __name__ == "__main__":
    # A range of tests, without a dependency on a test suite.

    o = Octree()

    internalPos = (100000, 100, 100)
    internalValue = "TEST-VALUE-1"

    externalPos = (-100000, 100, 100)
    externalValue = "TEST-VALUE-2"

    # Test that a lookup of a non-existant position fails.
    try:
        o.lookup(internalPos)
        raise RuntimeError("Bad test")
    except KeyError:
        pass

    # Test that a lookup of a non-existant position fails.
    try:
        o.lookup(externalPos)
        raise RuntimeError("Bad test")
    except KeyError:
        pass

    # Test that an insert within the initial bounds works.
    o.insert(internalPos, internalValue)

    # Ensure that the internal insert inserted the right value.
    if o.lookup(internalPos) != internalValue:
        raise RuntimeError("Bad test")

    # Test that an insert outside of the initial bounds works.
    o.insert(externalPos, externalValue)

    # Ensure that the external insert inserted the right value.
    if o.lookup(externalPos) != externalValue:
        raise RuntimeError("Bad test")

