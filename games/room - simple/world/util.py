import game.world

class ViewedObject(object):
    """
    Helper class that can be used as a formatting argument.
    
    This object when passed into a formatting string, can be referred to in
    different ways through the use of attributes on it.
    """

    def __init__(self, actor=None, viewer=None, object=None, verb=None):
        self._actor = actor
        self._viewer = viewer
        self._object = object
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
            if isinstance(self._object, game.world.Body):
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
