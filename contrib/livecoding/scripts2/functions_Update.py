# ...

def TestFunction(newargument):
    return (newargument,)

def TestFunction_PositionalArguments(newarg1, *newargs):
    return (newarg1, newargs)

def TestFunction_KeywordArguments(newarg1="newarg1", **newkwargs):
    return (newarg1, newkwargs)
