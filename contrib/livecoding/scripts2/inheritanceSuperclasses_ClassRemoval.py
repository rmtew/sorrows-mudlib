
class OldStyleBase:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def Func(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class NewStyleBase(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def Func(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class NewStyle(NewStyleBase):
    def __init__(self, *args, **kwargs):
        NewStyleBase.__init__(self, *args, **kwargs)

    def Func(self, *args, **kwargs):
        NewStyleBase.Func(self, *args, **kwargs)

    def FuncSuper(self, *args, **kwargs):
        super(NewStyle, self).Func(self, *args, **kwargs)
