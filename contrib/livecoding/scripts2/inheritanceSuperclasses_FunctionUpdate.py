# Purpose: ...

class OldStyleBase:
    """ Updated OldStyleBase doc string. """

    def __init__(self, *args, **kwargs):
        """ Updated OldStyleBase __init__ doc string """
    
        self.args = args
        self.kwargs = kwargs

    def Func(self, *args, **kwargs):
        """ Updated OldStyleBase Func doc string """

        self.args = args
        self.kwargs = kwargs

    def Func_Arguments1(self, newarg1, newkwarg1=False, *newargs, **newkwargs):
        return (newarg1, newkwarg1, newargs, newkwargs)

    def Func_Arguments2(self, arg1, kwarg1=True, *args, **kwargs):
        return (arg1, kwarg1, args, kwargs)

class NewStyleBase(object):
    """ Updated NewStyleBase doc string. """

    def __init__(self, *args, **kwargs):
        """ Updated NewStyleBase __init__ doc string """

        self.args = args
        self.kwargs = kwargs

    def Func(self, *args, **kwargs):
        """ Updated NewStyleBase Func doc string """

        self.args = args
        self.kwargs = kwargs

    def Func_Arguments1(self, newarg1, newkwarg1=False, *newargs, **newkwargs):
        """ Updated NewStyleBase Func_Arguments doc string """
        return (newarg1, newkwarg1, newargs, newkwargs)

    def Func_Arguments2(self, arg1, kwarg1=True, *args, **kwargs):
        return (arg1, kwarg1, args, kwargs)
