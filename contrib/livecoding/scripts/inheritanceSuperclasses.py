# Purpose: Implement base classes in order to test inheritance.

class OldStyleBase:
    """ OldStyleBase doc string. """

    def __init__(self, *args, **kwargs):
        """ OldStyleBase __init__ doc string """
    
        self.args = args
        self.kwargs = kwargs

    def Func(self, *args, **kwargs):
        """ OldStyleBase Func doc string """

        self.args = args
        self.kwargs = kwargs

    def Func_Arguments1(self, arg1, kwarg1=False, *args, **kwargs):
        return (arg1, kwarg1, args, kwargs)

    def Func_Arguments2(self, arg1, kwarg1=True, *args, **kwargs):
        return (arg1, kwarg1, args, kwargs)

class NewStyleBase(object):
    """ NewStyleBase doc string. """

    def __init__(self, *args, **kwargs):
        """ NewStyleBase __init__ doc string """

        self.args = args
        self.kwargs = kwargs

    def Func(self, *args, **kwargs):
        """ NewStyleBase Func doc string """

        self.args = args
        self.kwargs = kwargs

    def Func_Arguments1(self, arg1, kwarg1=False, *args, **kwargs):
        return (arg1, kwarg1, args, kwargs)

    def Func_Arguments2(self, arg1, kwarg1=True, *args, **kwargs):
        return (arg1, kwarg1, args, kwargs)

class OldStyle(OldStyleBase):
    def __init__(self, *args, **kwargs):
        OldStyleBase.__init__(self, *args, **kwargs)

    def Func(self, *args, **kwargs):
        OldStyleBase.Func(self, *args, **kwargs)

class NewStyle(NewStyleBase):
    def __init__(self, *args, **kwargs):
        NewStyleBase.__init__(self, *args, **kwargs)

    def Func(self, *args, **kwargs):
        NewStyleBase.Func(self, *args, **kwargs)

    def FuncSuper(self, *args, **kwargs):
        super(NewStyle, self).Func(self, *args, **kwargs)
