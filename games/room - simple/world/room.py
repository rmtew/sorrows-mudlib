import weakref

from mudlib import util
from game.world import Container, Body, Object

class ViewedActor:
    def __init__(self, actor, viewer, verb=None):
        self._actor = actor
        self._viewer = viewer
        self._verb = verb

    def SetViewer(self, viewer):
        self._viewer = viewer

    def __getattr__(self, attrName):
        attrNameLower = attrName.lower()
        
        if attrNameLower == "s":
            if self._actor is self._viewer:
                v = "you"
                if attrNameLower != attrName:
                    v = v.capitalize()
            else:
                v = self._actor.shortDescription
            return v
        elif attrNameLower == "v":
            if self._actor is self._viewer:
                v = self._verb
            else:
                v = self._verb +"s"
            return v

        raise AttributeError("%s instance has no attribute '%s'" % (self.__class__.__name__, attrName))

class Room(Container):
    def __init__(self):
        Container.__init__(self)
    
        self.exits = weakref.WeakValueDictionary()

    def AddExit(self, direction, room):
        direction = util.ResolveDirection(direction)
        self.exits[direction] = room

    def GetExits(self):
        return self.exits.keys()

    def GetExitRoom(self, direction):
        return self.exits.get(direction, None)

    def Message(self, msgfmt, *args):
        args = list(args)

        def SetArgsViewer(args, viewer):
            for i, arg in enumerate(args):
                if type(arg) is tuple:
                    actor, verb = arg
                    args[i] = ViewedActor(actor, viewer, verb)
                elif isinstance(arg, Object):
                    args[i] = ViewedActor(arg, viewer)
                elif isinstance(arg, ViewedActor):
                    args[i].SetViewer(viewer)

        for ob in self.contents:
            if isinstance(ob, Body):
                SetArgsViewer(args, ob)
                ob.user.Tell(msgfmt.format(*args))

import unittest

class ViewedActorTest(unittest.TestCase):
    def setUp(self):
        actor = self.actor = Body(None, None)
        actor.SetShortDescription("dwarf")

        self.otherViewer = Body(None, None)

        self.va = ViewedActor(actor, self.otherViewer, "verb")

    def test_ActorName(self):
        self.failUnless(self.va.s == "dwarf", "Viewer does not see actor by their short description as it is")
        self.failUnless(self.va.S == "dwarf", "Viewer does not see actor by their short description as it is")

        self.va.SetViewer(self.va._actor)
        
        self.failUnless(self.va.s == "you", "Actor does not see themselves as the lowercase 'you'")
        self.failUnless(self.va.S == "You", "Actor does not see themselves as the capitalised 'you'")

    def test_Verb(self):
        self.failUnless(self.va.v == "verbs", "Viewer does not see the verb in the correct form")

        self.va.SetViewer(self.va._actor)

        self.failUnless(self.va.v == "verb", "Actor does not see the verb in the correct form")
