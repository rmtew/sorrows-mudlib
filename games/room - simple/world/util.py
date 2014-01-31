import textsupport
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
        Capitalised versions of these give the capitalised result.
        s  - Short description.
        pn - Pronoun.
        v  - Verb.
        """
        attrNameLower = attrName.lower()

        if self._object is self._viewer:
            text = "you"
            if attrNameLower == "v":
                text = self._verb
        elif attrNameLower == "s":
            #   If the object is a body, use their short description directly.
            text = self._object.shortDescription
            if isinstance(self._object, game.world.Body):
                pass
            #   If the viewer is the actor, use the description with "the" article.
            elif self._viewer is self._actor:
                text = "the "+ text
            #   If the viewer is not the actor, use the description with "a"/"an" article.
            elif text[0] in ("a", "e", "i", "o", "u"):
                text = "an "+ text
            else:
                text = "a "+ text
        elif attrNameLower == "pn":
            text = self._object.GetPronoun()
        elif attrNameLower == "v":
            text = textsupport.pluralise(self._verb)
        else:
            raise AttributeError("%s instance has no attribute '%s'" % (self.__class__.__name__, attrName))

        if attrName != attrNameLower:
            return text.capitalize()
        return text
