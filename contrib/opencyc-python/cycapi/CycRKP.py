## module CycRKP

## Interface to Rapid Knowledge Population functionality

import CycConnection
import CycObject

## The following class contains methods that interface to functions
## in oopopscript.lisp, a module written by Stefano Bertolo.

class CycKnowledgePopulator (CycConnection.CycAccess):

    def __init__ (self, hostName, basePort):
        CycConnection.CycAccess.__init__(self, hostName, basePort)
        # Loading the oopopscript modules here  is a temporary measure that is
        # not portable (i.e. will not work outside of Cycorp).
        #script = "(load /cyc/projects/aquaint/ibm-cyc-proposal/oopopscript.lisp)"
        #return self.converseString(script)

    def findUnitsForPred (self, pred):
        script = "(find-units-for-pred " + pred.stringApiValue() + ")" + "\r\n"
        result = self.converseList(script)
        result = result.data[0].data[1]
        return result

    def findCollectionPredicates (self, collection):
        script = "(find-collection-predicates " + collection.stringApiValue() + ")" + "\r\n"
        result = self.converseList(script)
        return result


















