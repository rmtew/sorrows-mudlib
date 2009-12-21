# Purpose: Implement subclasses in order to test inheritance.

import game

OldStyleBase = game.OldStyleBase
NewStyleBase = game.NewStyleBase

class OldStyleSubclassViaNamespace(game.OldStyleBase):
    def __init__(self, *args, **kwargs):
        game.OldStyleBase.__init__(self, *args, **kwargs)

    def Func(self, *args, **kwargs):
        game.OldStyleBase.Func(self, *args, **kwargs)

class NewStyleSubclassViaNamespace(game.NewStyleBase):
    def __init__(self, *args, **kwargs):
        game.NewStyleBase.__init__(self, *args, **kwargs)

    def Func(self, *args, **kwargs):
        game.NewStyleBase.Func(self, *args, **kwargs)

    def FuncSuper(self, *args, **kwargs):
        super(game.NewStyleSubclassViaNamespace, self).Func(*args, **kwargs)

class OldStyleSubclassViaGlobalReference(OldStyleBase):
    def __init__(self, *args, **kwargs):
        OldStyleBase.__init__(self, *args, **kwargs)

    def Func(self, *args, **kwargs):
        OldStyleBase.Func(self, *args, **kwargs)

class NewStyleSubclassViaGlobalReference(NewStyleBase):
    def __init__(self, *args, **kwargs):
        NewStyleBase.__init__(self, *args, **kwargs)

    def Func(self, *args, **kwargs):
        NewStyleBase.Func(self, *args, **kwargs)

    def FuncSuper(self, *args, **kwargs):
        super(NewStyleSubclassViaGlobalReference, self).Func(*args, **kwargs)

class NewStyleSubclassViaClassReference(NewStyleBase):
    def __init__(self, *args, **kwargs):
        self.__class__.__bases__[0].__init__(self, *args, **kwargs)

    def Func(self, *args, **kwargs):
        self.__class__.__bases__[0].Func(self, *args, **kwargs)
