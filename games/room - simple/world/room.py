import weakref

from mudlib import util
from game.world import Container, Body, Object

class ViewedObject(object):
    """
    Helper class that can be used as a formatting argument.
    
    This object when passed into a formatting string, can be referred to in
    different ways through the use of attributes on it.
    """

    def __init__(self, actor, viewer, object_, verb=None):
        self._actor = actor
        self._viewer = viewer
        self._object = object_
        self._verb = verb

    def __getattr__(self, attrName):
        """
        s - Short description.
        S - Short description (capitalised).
        v - Verb.
        """

        if attrName in ("s", "S"):
            if self._object is self._viewer:
                if attrName == "S":
                    return "You"
                return "you"

                #   If the object is a body, use their short description directly.
            text = self._object.shortDescription
            if isinstance(self._object, Body):
                return text
            #   If the viewer is the actor, use the description with "the" article.
            if self._viewer is self._actor:
                return "the "+ text
            #   If the viewer is not the actor, use the description with "a"/"an" article.
            if text[0] in ("a", "e", "i", "o", "u"):
                return "an "+ text
            return "a "+ text

        if attrName == "v":
            if self._object is self._viewer:
                return self._verb
            return self._verb +"s"

        raise AttributeError("%s instance has no attribute '%s'" % (self.__class__.__name__, attrName))

class Room(Container):
    def __init__(self):
        Container.__init__(self)
    
        self.exits = weakref.WeakValueDictionary()

    def AddExit(self, direction, room):
        direction = util.ResolveDirection(direction)
        self.exits[direction] = room

    def GetExitRoom(self, direction):
        return self.exits.get(direction, None)

    def LookString(self, viewer):
        s = self.shortDescription +"\r\n"
        s += Container.LookString(self, viewer)

        exitNames = self.exits.keys()
        exitNames.sort()
        if len(exitNames):
            t = ", ".join(exitNames)
        else:
            t = "None"
        s += "\r\nExits: "+ t

        return s

    def Message(self, context, msgfmt, *args):
        def SetArgsViewer(args, viewer):
            l = list(args)
            for i, arg in enumerate(args):
                if type(arg) is tuple:
                    object, verb = arg
                    l[i] = ViewedObject(context.body, viewer, object, verb)
                elif isinstance(arg, Object):
                    l[i] = ViewedObject(context.body, viewer, arg)
                else:
                    l[i] = arg
            return l
                    
        for ob in self.contents:
            if isinstance(ob, Body):
                formatArgs = SetArgsViewer(args, ob)
                ob.user.Tell(msgfmt.format(*formatArgs))

import unittest

class ViewedObjectTest(unittest.TestCase):
    longMessage = True

    def setUp(self):
        # Viewing body.
        self.viewingBody = Body(None, None)

        # Viewed body.
        self.viewedBody = Body(None, None)
        self.viewedBody.SetShortDescription("dwarf")
        
        # Viewed "a" article object / "an" article object.
        self.aArticleObject = Object("sword")
        self.anArticleObject = Object("apple")

        # ViewedObject(ACTOR, VIEWER, OBJECT)
        self.bodyIndirectPerspective = ViewedObject(self.viewingBody, self.viewingBody, self.viewedBody, "verb")
        self.bodyDirectPerspective = ViewedObject(self.viewingBody, self.viewingBody, self.viewingBody, "verb")

    def testObjectArticle(self):
        # Watching someone 'take a sword' should result in display of "a sword".
        aPerspective = ViewedObject(self.viewedBody, self.viewingBody, self.aArticleObject, "verb")
        self.assertEqual(aPerspective.s, "a sword")

        # Watching someone 'take an apple' should result in display of "an apple".
        anPerspective = ViewedObject(self.viewedBody, self.viewingBody, self.anArticleObject, "verb")
        self.assertEqual(anPerspective.s, "an apple")

        # Seeing yourself 'take an apple' should result in display of "the apple".
        thePerspective = ViewedObject(self.viewedBody, self.viewedBody, self.anArticleObject, "verb")
        self.assertEqual(thePerspective.s, "the apple")
        
    def testActorName(self):
        self.assertEqual(self.bodyIndirectPerspective.s, "dwarf", "Actor does not see viewed body by the short description")
        self.assertEqual(self.bodyIndirectPerspective.S, "dwarf", "Actor does not see viewed body by the uncapitalised short description")
        
        self.assertEqual(self.bodyDirectPerspective.s, "you", "Actor does not see themselves as the lowercase 'you'")
        self.assertEqual(self.bodyDirectPerspective.S, "You", "Actor does not see themselves as the capitalised 'you'")

    def testVerb(self):
        self.assertEqual(self.bodyIndirectPerspective.v, "verbs", "Viewer does not see the verb in the correct form")
        self.assertEqual(self.bodyDirectPerspective.v, "verb", "Actor does not see the verb in the correct form")
