import weakref

from mudlib import util
from game.world import ViewedObject
from game.world import Container, Body, Object


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
                    l[i] = ViewedObject(actor=context.body, viewer=viewer, object=object, verb=verb)
                elif isinstance(arg, Object):
                    l[i] = ViewedObject(actor=context.body, viewer=viewer, object=arg)
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
        self.bodyIndirectPerspective = ViewedObject(actor=self.viewingBody, viewer=self.viewingBody, object=self.viewedBody, verb="verb")
        self.bodyDirectPerspective = ViewedObject(actor=self.viewingBody, viewer=self.viewingBody, object=self.viewingBody, verb="verb")

    def testObjectArticle(self):
        # Watching someone 'take a sword' should result in display of "a sword".
        aPerspective = ViewedObject(actor=self.viewedBody, viewer=self.viewingBody, object=self.aArticleObject, verb="verb")
        self.assertEqual(aPerspective.s, "a sword")

        # Watching someone 'take an apple' should result in display of "an apple".
        anPerspective = ViewedObject(actor=self.viewedBody, viewer=self.viewingBody, object=self.anArticleObject, verb="verb")
        self.assertEqual(anPerspective.s, "an apple")

        # Seeing yourself 'take an apple' should result in display of "the apple".
        thePerspective = ViewedObject(actor=self.viewedBody, viewer=self.viewedBody, object=self.anArticleObject, verb="verb")
        self.assertEqual(thePerspective.s, "the apple")
        
    def testActorName(self):
        self.assertEqual(self.bodyIndirectPerspective.s, "dwarf", "Actor does not see viewed body by the short description")
        self.assertEqual(self.bodyIndirectPerspective.S, "dwarf", "Actor does not see viewed body by the uncapitalised short description")
        
        self.assertEqual(self.bodyDirectPerspective.s, "you", "Actor does not see themselves as the lowercase 'you'")
        self.assertEqual(self.bodyDirectPerspective.S, "You", "Actor does not see themselves as the capitalised 'you'")

    def testVerb(self):
        self.assertEqual(self.bodyIndirectPerspective.v, "verbs", "Viewer does not see the verb in the correct form")
        self.assertEqual(self.bodyDirectPerspective.v, "verb", "Actor does not see the verb in the correct form")
