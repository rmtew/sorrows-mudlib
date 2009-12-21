# ...

def TestFunction(argument):
    return (argument,)

def TestFunction_PositionalArguments(arg1, *args):
    return (arg1, args)

def TestFunction_KeywordArguments(arg1="arg1", **kwargs):
    return (arg1, kwargs)
