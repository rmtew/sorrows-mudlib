# module CycObjectFactory

"""
So far, this module is only implemented enough so that method
calls can run without error. Usually, this will mean returning
the value: None.
"""

class CycObjectFactory:
    def __init__ (self):
        pass

    def makeCycSymbol (self, symbolNameAnyCase):
        return None
    def getCycSymbolCache (self, symbolName):
        return None
    def removeCycSymbolCache (self, cycSymbol):
        return None
    def getCycSymbolCacheSize (self):
        return None
    def resetCaches (self):
        return None
    def resetCycConstantCaches (self):
        return None
    def addCycConstantCacheByName (self, cycConstant):
        return None
    def addCycConstantCacheByGuid (self, cycConstant):
        return None
    def getCycConstantCacheByName (self, name):
        return None
    def removeChaches (self):
        return None
    def getCycConstantCacheByNameSize (self):
        return None
    def resetCycNartCache (self):
        return None
    def addCycNartCache (self, cycNart):
        return None
    def getCycNartCache (self, name):
        #parameter was id, needs to be converted
        return None
    def removeCycNartCache (self, cycNart):
        return None
    def getCycNartCacheSize (self):
        return None
    def resetAssertionCache (self):
        return None
    def addAssertionCache (self, cycAssertion):
        return None
    def getAssertionCache (self, guid):
        #parameter was id, need to be converted
        return None
    def removeAssertionCache (self, guid):
        #parameter was id, need to be converted
        return None
    def getAssertionCacheSize (self):
        return None
    def makeCycVariable (self, name):
        return None
    def makeUniqueCycVariable (self, modelCycVariable):
        return None
    def resetCycVariableCache (self):
        return None
    def addCycVariableCache (self, cycVariable):
        return None
    def getCycVariableCache (self, name):
        return None
    def removeCycVariableCache (self, cycVariable):
        return None
    def getCycVariableCacheSize (self):
        return None
    def makeGuid (self, guidString):
        return None
    def addGuidCache (self, guid):
        return None
    def resetGuidCache (self):
        return None
    def getGuidCache (self, guidName):
        return None
    def removeGuidCache (self, guid):
        return None
    def getGuidCacheSize (self):
        return None
    def unmarshall (self, xmlString):
        return None
    def unmarshallElement (self, element, document):
        return None
    def unmarshallGuid (self, guidElement):
        return None
    def unmarshallCycSymbol (self, cycSymbolElement):
        return None
    def unmarshallCycAssertion (self, cycAssertionElement):
        return None
    def unmarshallCycVariable (self, cycVariableElement):
        return None
    def unmarshallCycConstant (self, cycConstantElement, document):
        return None
    def unmarshallCycNart (self, cycNartElement, document):
        return None
    def unmarshallCycList (self, cycListElement, document):
        return None
    def unmarshallByteArray (self, byteArrayElement, document):
        return None
