# module CycConnection --

import sys
from string import split,rstrip, replace
from socket import *
from CycObject import *
from CycListParser import *
import CycObjectFactory

NO_VERBOSITY = 0
LOW_VERBOSITY = 5
MEDIUM_VERBOSITY = 10
HIGH_VERBOSITY = 15
DEFAULT_VERBOSITY = LOW_VERBOSITY
VERBOSITY = NO_VERBOSITY
# For methods, functions on the STUB_LIST,
# use the 'stub' branch of the code.
STUB_LIST = ['test']
VERBOSITY_DICT = {}

baseKB = 4
isa = None
genls = None
genlMt = None
comment = None
collection = None
binaryPredicate = None
elementOf = None
numericallyEqual = None
plusFn = None
different = None
thing = None
inferencePSC = None
universalVocabularyMt = None
bookkeepingMt = None

# module TracedObject

class TracedObject:

    stubList = STUB_LIST
    verbosityDict = VERBOSITY_DICT

    def __init__(self,
                 objectVerbosity = DEFAULT_VERBOSITY):
        self.verbosity = objectVerbosity

    def checkVerbosity(self):

        return (self.verbosity >= VERBOSITY) or \
            self.verbosityDict.has_key(self.verbosity)

    def outputIfTraced(self, outString=''):

        if self.checkVerbosity():
            if outString != '':
                print self.verbosity,">  trace:",self
                print self.verbosity,">  traceinfo: ",outString
            else:
                print self.verbosity,">  trace:",self


class CycApiObject(TracedObject):

    def __init__(self, objectVerbosity=DEFAULT_VERBOSITY):

        if objectVerbosity:
            TracedObject.__init__(self, objectVerbosity)
        else:
            TracedObject.__init__(self)


# module CycAccess

cycConnection = '' # used for persistent connections
ASCII_MODE = 1
BINARY_MODE = 2
COMMUNICATION_MODE = ASCII_MODE
DEFAULT_HOSTNAME = 'localhost'
DEFAULT_BASE_PORT = 3600
PERSISTENT_CONNECTION = 0
MESSAGING_MODE = 0

class CycAccess(CycApiObject):

    def type(self): return 'CycAccess'

    def __init__ (self,
              hostName=DEFAULT_HOSTNAME,
              basePort=DEFAULT_BASE_PORT,
              communicationMode=COMMUNICATION_MODE,
              persistentConnection=PERSISTENT_CONNECTION,
              messagingMode=MESSAGING_MODE):
        CycApiObject.__init__(self)
        if persistentConnection:
            cycConnection = CycConnection(self.hostName,
                              self.port,
                              self.communicationMode,
                              self.messagingMode,
                              self)
        self.hostName = hostName
        self.port = basePort
        self.communicationMode = communicationMode
        self.persistentConnection = persistentConnection
        self.messagingMode = messagingMode
        self.cycObjectFactory = CycObjectFactory.CycObjectFactory()

        #self.commonInitialization()

    def __str__ (self):
        return(str([self.hostName,self.port,self.communicationMode,
                self.persistentConnection,self.messagingMode]))

    def commonInitialization (self):
        # self.initializeConstants()
        pass

    def close (self):
        if (cycConnection != ''):
        #to do: determine is cycConnection is an instance of RemoteCycConnection
            cycConnection.close()

    def converse (self, command):
        if not self.persistentConnection:
            cycConnection = CycConnection(self.hostName,
                              self.port,
                              self.communicationMode,
                              self.messagingMode,
                              self)
            response = cycConnection.converse(command)
            cycConnection.close()
        return response

    def converseObject (self, command):
        response = self.converse(command)
        if response[0]:
            return response[1]
        else:
            if isinstance(command, CycObject.CycList):
                request = command.cyclify
            else:
                request = str(command)
            # the following should really be a CycApiException,
            # but that hasn't been created yet
            raise TypeError, request + "in CycAccess.converseObject()"

    def converseList (self, command):
        response = self.converse(command)
        if response[0] == "Error:":
            raise TypeError, "Expected non-error but received (" + str(response[1]) + ")"
        elif response[0]:
            if response[1] == 'NIL':
                return CycList([])
            else:
                result = CycListParser(response[1]).makeCycList()
                return result[1]
        else:
            if isinstance(command, CycObject.CycList):
                request = CycList(command).cyclify()
            else:
                request = string(command)
            raise TypeError, request + " in CycAccess.converseList()"

    def converseString (self, command):
        response = self.converse(command)
        if response[0]:
            if type(response[1]) is not str:
                raise TypeError, "Expected string but received (" + str(response[1]) + ")"
            return response[1]
        else:
            if isinstance(command, CycObject.CycList):
                request = command.cyclify()
            else:
                request = command
            raise TypeError, response[1].toString() + "\r\nrequest: " + request

    def converseBoolean (self, command):
        response = self.converse(command)
        if response[0]:
            if (response[1].toString().equals("T")):
                return 1 # return true
            else:
                return 0 # reutrn false

    def converseInt (self, command):
        response = self.converse(command)
        if response[0]:
            return int(response[1].toString())

    def converseVoid (self, command):
        response = self.converse(command)
        if not response[0]:
            if isinstance(command, CycObject.CycList):
                request = command.cyclify()
            else:
                request = command
            raise TypeError, response[1].toString() + "\r\nrequest: " + request

##  I get a name error on any of the global variables used within initializeConstants.
##  It seems that this method won't recognize 'isa' as a global, even though 'isa'
##  works fine in the method commonInitialization.
##
##        def initializeConstants (self):
##            print "test3:",isa
##          if (self.baseKB == None):
##                self.baseKB = self.getKnownConstantByGuid("bd588111-9c29-11b1-9dad-c379636f7270")
##            if isa == 2:
##                isa = self.getKnownConstantByGuid("bd588104-9c29-11b1-9dad-c379636f7270")
##            if (genls == None):
##                genls = self.getKnownConstantByGuid("bd58810e-9c29-11b1-9dad-c379636f7270")
##            if (genlMt == None):
##                genlMt = self.getKnownConstantByGuid("bd5880e5-9c29-11b1-9dad-c379636f7270")
##            if (comment == None):
##                comment = self.getKnownConstantByGuid("bd588109-9c29-11b1-9dad-c379636f7270")
##            if (collection == None):
##                collection = self.getKnownConstantByGuid("bd5880cc-9c29-11b1-9dad-c379636f7270")
##            if (binaryPredicate == None):
##                binaryPredicate = self.getKnownConstantByGuid("bd588102-9c29-11b1-9dad-c379636f7270")
##            if (elementOf == None):
##                elementOf = self.getKnownConstantByGuid("c0659a2b-9c29-11b1-9dad-c379636f7270")
##      #########################
##            # These are reserved in python. We need another name else skip them.
##            # if (and == None):
##            #     and = self.getKnownConstantByGuid("bd5880f9-9c29-11b1-9dad-c379636f7270")
##            # if (or == None):
##            #     or = self.getKnownConstantByGuid("bd5880fa-9c29-11b1-9dad-c379636f7270")
##            # if (not == None):
##            #     not = self.getKnownConstantByGuid("bd5880fb-9c29-11b1-9dad-c379636f7270")
##            ##########################
##            #if (numericallyEqual == None):
##            #    //numericallyEqual = self.getKnownConstantByGuid("bd589d90-9c29-11b1-9dad-c379636f7270")
##            #    numericallyEqual = getConstantByGuid(new Guid("bd589d90-9c29-11b1-9dad-c379636f7270"))
##            if (plusFn == None):
##                plusFn = self.getKnownConstantByGuid("bd5880ae-9c29-11b1-9dad-c379636f7270")
##            if (different == None):
##                different = self.getKnownConstantByGuid("bd63f343-9c29-11b1-9dad-c379636f7270")
##            if (thing == None):
##                thing = self.getKnownConstantByGuid("bd5880f4-9c29-11b1-9dad-c379636f7270")
##            if (inferencePSC == None):
##                inferencePSC = self.getKnownConstantByGuid("bd58915a-9c29-11b1-9dad-c379636f7270")
##            if (universalVocabularyMt == None):
##                universalVocabularyMt = self.getKnownConstantByGuid("dff4a041-4da2-11d6-82c0-0002b34c7c9f")
##            if (bookkeepingMt == None):
##                bookkeepingMt = self.getKnownConstantByGuid("beaed5bd-9c29-11b1-9dad-c379636f7270")



    def getKnownConstantByName (self, constantName):
        cycConstant = self.getConstantByName(constantName)
        if not cycConstant:
            raise ValueError, "Expected constant not found " + constantName
        return cycConstant

    def getConstantByName (self, constantName):
        name = self.uncyclify(constantName)
        #insert code to check a cache for constant and retrieve if there.
        answer = CycObject.CycConstant(name)
#       use of internal ids is deprecated
#       id = self.getConstantId(name)
#       if not id:
#           return 0 # constant not found
        guid = self.getConstantGuid(name)
        if not guid:
            return 0 #constant not found
        answer.guid = guid
        #insert code to add `answer` to the CycConstant by Name cache
        return answer

    def getConstantID (self, arg1):
        # use of internal IDs is deprecated
        pass

    def getConstantGuid (self, arg1):
        if type(arg1) == type(''):
            command = '(guid-to-string (constant-external-id (find-constant "' \
            + arg1 + '")))'
            ans = self.converseString(command)
            return CycObject.Guid(ans)
        elif (str(type(arg1)) == "<type 'instance'>") and isinstance(command, CycObject.CycConstant):
            self.getConstantGuid(arg1.name)
        else:
            raise TypeError, "expected string or CycConstant instance"

    def getConstantByID (self, id):
        # use of internal IDs is deprecated
        #convert this to use guids if possible
        pass

    def getConstantName (self, id):
        # use of internal IDs is deprecated
        #convert this to use guids if possible
        pass

    def getVariableName (self, id):
        # use of internal IDs is deprecated
        #convert this to use guids if possible
        pass

    def getKnownConstantByGuid (self, arg1):
        if type(arg1) == type(''):
            guid = CycObject.Guid(arg1)
            return self.getKnownConstantByGuid(guid)
        elif (str(type(command)) == "<type 'instance'>") and isinstance(command, CycObject.Guid):
            cycConstant = self.getConstantByGuid(arg1)
            if cycConstant == None:
                raise TypeError, "Expected constant not found"
            return cycConstant

    def getConstantByGuid (self, arg1):
        if type(arg1) == type(''):
            guidString = arg1
        elif (str(type(command)) == "<type 'instance'>") and isinstance(command, CycObject.Guid):
            guidString = arg1.guidString
        command = '(boolean (find-constant-by-external-id (string-to-guid "' \
        + guidString + '")))'
        constantExists = self.converseBoolean(command)
        if not constantExists:
            return None
        command = '(constant-name (find-constant-by-external-id (string-to-guid "' \
        + guidString + '")))'
        constantName = self.converseString(command)
        return self.getConstantByName(constantName)

    def getComment (self, cycFort, mt = None):
        if mt == None: mt = inferencePSC
        script = \
        "(clet ((comment-string \n" + \
        "        (comment " + cycFort.stringApiValue() + mt.stringApiValue() + "))) \n" \
        "  (fif comment-string \n" + \
        "       (string-substitute \" \" \"\\\"\" comment-string) \n" + \
        "       \"\"))"
        return self.converseString(script)

    def completeObject (self, object):
        if (str(type(object)) == "<type 'instance'>"):
            if isinstance(object, CycObject.CycConstant):
                return self.completeCycConstant(object)
            elif isinstance(object, CycObject.CycList):
                return self.completeCycList(object)
            elif isinstance(object, CycObject.CycNart):
                return self.completeCycNart(object)
            elif isinstance(object, CycObject.CycAssertion):
                return self.completeCycAssertion(object)
            else:
                return object
        else:
            raise TypeError, "Expected an object"

    def completeCycConstant (self, cycConstant):
        cachedConstant = self.cycObjectFactory.getCycConstantCacheByName(cycConstant.name)
        if cachedConstant == None:
            cycConstant.setGuid(getConstantGuid(cycConstant.name))
            self.cycObjectFactory.addCycConstantCacheByName(cycConstant)
            return cycConstant
        else:
            return cachedConstant

    def completeCycVariable (self, cycVariable):
        pass

    def completeCycList (self, cycList):
        pass

    def completeCycNart (self, cycNart):
        pass

    def completeCycAssertion (self, cycAssertion):
        pass

    def getImprecisePluralGeneratedPhrase (self, cycFort):
        ans = self.converseString("(with-precise-paraphrase-off (generate-phrase " + \
        cycFort.stringApiValue() + " '(#$plural)))\r\n")
        return ans[1:-1]

    def getPluralGeneratedPhrase (self, cycFort):
        ans = self.converseString("(with-precise-paraphrase-on (generate-phrase " + \
        cycFort.stringApiValue() + " '(#$plural)))\r\n")
        return ans[1:-1]

    def getImpreciseSingularGeneratedPhrase (self, cycFort):
        ans = self.converseString("(with-precise-paraphrase-off (generate-phrase " + \
        cycFort.stringApiValue() + " '(#$singular)))\r\n")
        return ans[1:-1]

    def getSingularGeneratedPhrase (self, cycFort):
        ans = self.converseString("(with-precise-paraphrase-on (generate-phrase " + \
        cycFort.stringApiValue() + " '(#$singular)))\r\n")
        return ans[1:-1]

    def getGeneratedPhrase (self, cycFort):
        ans = self.converseString("(with-precise-paraphrase-on (generate-phrase " + \
        cycFort.stringApiValue() + "))\r\n")
        return ans[1:-1]

    def getParaphrase (self, assertion):
        ans = self.converseString("(with-precise-paraphrase-on (generate-phrase '" + \
        assertion.cyclify() + "))\r\n")
        return ans[1:-1]

    def getImpreciseParaphrase (self, assertion):
        ans = self.converseString("(with-precise-paraphrase-off (generate-phrase '" + \
        assertion.cyclify() + "))\r\n")
        return ans[1:-1]

##         def getComment (self, cycFort, mt):
##             ########################
##             # This is supposed to handle converting embedded quotes in the comment to spaces,
##             # but I'm not yet getting the embedded quotes in the script string correct.
##             #script = \
##             #'(clet ((comment-string \n' + \
##             #'         (comment ' + cycFort.stringApiValue() + ' ' + mt.stringApiVlaue() + \
##             #'))) \n' + \
##             #'   (fif comment-string \n' + \
##             #'        (string-substitute " " "\"" comment-string) \n" + \
##             #'        \"\"))'
##             ###################
##             script = "(comment " + cycFort.stringApiValue() + ' ' + mt.stringApiValue() + ")"
##             return self.converseString(script)

    def getIsas (self, cycFort, mt = None):
        if mt == None:
            return self.converseList("(remove-duplicates (with-all-mts (isa " + \
            cycFort.stringApiValue() + ")))")
        else:
            return self.converseList("(isa " + cycFort.stringApiValue() + \
            " " + mt.stringApiValue() + ")")

    def getGenls (self, cycFort, mt = None):
        if mt == None:
            return self.converseList("(remove-duplicates (with-all-mts (genls " + \
            cycFort.stringApiValue() + ")))")
        else:
            return self.converseList("(genls " + cycFort.stringApiValue() + \
            " " + mt.stringApiValue() + ")")

    def getMinGenls (self, cycFort, mt = None):
        if mt == None:
            return self.converseList("(remove-duplicates (with-all-mts (min-genls " + \
            cycFort.stringApiValue() + ")))")
        else:
            return self.converseList("(min-genls " + cycFort.stringApiValue() + \
            " " + mt.stringApiValue() + ")")

    def getSpecs (self, cycFort, mt = None):
        if mt == None:
            return self.converseList("(remove-duplicates (with-all-mts (specs " + \
            cycFort.stringApiValue() + ")))")
        else:
            return self.converseList("(specs " + cycFort.stringApiValue() + \
            " " + mt.stringApiValue() + ")")

    def getMaxSpecs (self, cycFort, mt = None):
        if mt == None:
            return self.converseList("(remove-duplicates (with-all-mts (max-specs " + \
            cycFort.stringApiValue() + ")))")
        else:
            return self.converseList("(max-specs " + cycFort.stringApiValue() + \
            " " + mt.stringApiValue() + ")")

    def getGenlSiblings (self, cycFort, mt = None):
        if mt == None:
            return self.converseList("(remove-duplicates (with-all-mts (genl-siblings " + \
            cycFort.stringApiValue() + ")))")
        else:
            return self.converseList("(genl-siblings " + cycFort.stringApiValue() + \
            " " + mt.stringApiValue() + ")")

    def getSiblings (self, cycFort, mt = None):
        getSpecSiblings(self, mt)

    def getSpecSiblings (self, cycFort, mt = None):
        if mt == None:
            return self.converseList("(remove-duplicates (with-all-mts (spec-siblings " + \
            cycFort.stringApiValue() + ")))")
        else:
            return self.converseList("(spec-siblings " + cycFort.stringApiValue() + \
            " " + mt.stringApiValue() + ")")

    def getAllGenls (self, cycFort, mt = None):
        if mt == None:
            return self.converseList("(remove-duplicates (with-all-mts (all-genls " + \
            cycFort.stringApiValue() + ")))")
        else:
            return self.converseList("(all-genls " + cycFort.stringApiValue() + \
            " " + mt.stringApiValue() + ")")

    def getAllSpecs (self, cycFort, mt = None):
        if mt == None:
            return self.converseList("(remove-duplicates (with-all-mts (all-specs " + \
            cycFort.stringApiValue() + ")))")
        else:
            return self.converseList("(all-specs " + cycFort.stringApiValue() + \
            " " + mt.stringApiValue() + ")")

    def getAllGenlsWrt (self, spec, genl, mt = None):
        if mt == None:
            return self.converseList("(remove-duplicates (with-all-mts (all-genls-wrt " + \
            spec.stringApiValue() + " " + genl.stringApiValue() + ")))")
        else:
            return self.converseList("(all-genls-wrt " + spec.stringApiValue() + \
            " " + genl.stringApiValue() + " " + mt.stringApiValue() + ")")

    def getAllDependentSpecs (self, cycFort, mt = None):
        if mt == None:
            return self.converseList("(remove-duplicates (with-all-mts (all-dependent-specs " + \
            cycFort.stringApiValue() + ")))")
        else:
            return self.converseList("(all-dependent-specs " + cycFort.stringApiValue() + \
            " " + mt.stringApiValue() + ")")

    def getSampleLeafSpecs (self, cycFort, numberOfSamples, mt = None):
        if mt == None:
            return self.converseList("(with-all-mts (sample-leaf-specs " + \
            cycFort.stringApiValue() + " " + str(numberOfSamples) + "))")
        else:
            return self.converseList("(sample-leaf-specs " + cycFort.stringApiValue() + \
            " " + str(numberOfSamples) + " " + mt.stringApiValue() + ")")

    # Returns the single most specific collection from the given list of collections.
    #
    # @param collections a CycList of the given collections
    def getMinCol (self, collections):
        return self.converseObject("(with-all-mts (min-col " + \
        collections.stringApiValue() + "))")

    def isSpecOf (self, spec, genl, mt = None):
        if mt == None:
            return isGenlOf(genl, spec)
        else:
            return isGenlOf(genl, spec, mt)

    def isGenlOf (self, genl, spec, mt = None):
        if mt == None:
            return self.converseBoolean("(genl-in-any-mt? " + \
            spec.stringApiValue() + " " + genl.stringApiValue() + ")")
        else:
            return self.converseBoolean("(genl? " + spec.stringApiValue() + " " + \
            genl.stringApiValue() + " " + mt.stringApiValue() + ")")

    def isGenlPredOf (self, genlPred, specPred, mt = None):
        if mt == None:
            return self.converseBoolean("(with-all-mts (genl-predicate? " + \
            spec.stringApiValue() + " " + genl.stringApiValue() + "))")
        else:
            return self.converseBoolean("(genl-predicate? " + specPred.stringApiValue() + " " \
            + genlPred.stringApiValue() + " " + mt.stringApiValue() + ")")

    def isGenlInverseOf (self, genlPred, specPred, mt = None):
        if mt == None:
            return self.converseBoolean("(with-all-mts (genl-inverse? " + \
            specPred.stringApiValue() + " " + genlPred.stringApiValue + "))")
        else:
            return self.converseBoolean("(genl-inverse? " + specPred.stringApiValue() + " " + \
            genlPred.stringApiValue + " " + mt.stringApiValue() + ")")

    def isGenlMtOf (self, genlMt, specMt):
        return converseBoolean("(genl-mt? " + specMt.stringApiValue() + " " \
        + genlMt.stringApiValue() + ")")

    def getCollectionLeaves (self, cycFort, mt = None):
        if mt == None:
            return self.converseList("(with-all-mts (collection-leaves " + \
            cycFort.stringApiValue() + "))")
        else:
            return self.converseList("(collection-leaves " + cycFort.stringApiValue() + \
            " " + mt.stringApiValue() + ")")

    def areDisjoint (self, collection1, collection2, mt = None):
        if mt == None:
            return self.converseBoolean("(with-all-mts (disjoint-with? " + \
            collection1.stringApiValue() + " " + collection2.stringApiValue() + "))")
        else:
            return self.converseBoolean("(disjoint-with? " + collection1.stringApiValue() + \
            " " + collection2.stringApiValue + " " + mt.stringApiValue() + ")")

####################################
## not done yet. Bodies of methods are pasted from method 'isa' above
##
##        def getMinIsas (self, cycFort, mt = None):
##            if mt == None:
##                return self.converseList("(remove-duplicates (with-all-mts (isa " + \
##                cycFort.stringApiValue() + ")))")
##            else:
##                return self.converseList("(isa " + cycFort.stringApiValue() + \
##                " " + mt.stringApiValue() + ")")
##
##        def getInstances (self, cycFort, mt):
##            if mt == None:
##                return self.converseList("(remove-duplicates (with-all-mts (isa " + \
##                cycFort.stringApiValue() + ")))")
##            else:
##                return self.converseList("(isa " + cycFort.stringApiValue() + \
##                " " + mt.stringApiValue() + ")")
##
##        def getInstanceSiblings (self, cycFort, mt = None):
##            if mt == None:
##                return self.converseList("(remove-duplicates (with-all-mts (isa " + \
##                cycFort.stringApiValue() + ")))")
##            else:
##                return self.converseList("(isa " + cycFort.stringApiValue() + \
##                " " + mt.stringApiValue() + ")")
##
##        def getAllIsa (self, cycFort, mt = None):
##            if mt == None:
##                return self.converseList("(remove-duplicates (with-all-mts (isa " + \
##                cycFort.stringApiValue() + ")))")
##            else:
##                return self.converseList("(isa " + cycFort.stringApiValue() + \
##                " " + mt.stringApiValue() + ")")
##
##        def getAllInstances (self, cycFort, mt = None):
##            if mt == None:
##                return self.converseList("(remove-duplicates (with-all-mts (isa " + \
##                cycFort.stringApiValue() + ")))")
##            else:
##                return self.converseList("(isa " + cycFort.stringApiValue() + \
##                " " + mt.stringApiValue() + ")")
##
##        def isa (term, collection, mt = None):
##            if mt == None:
##                return self.converseList("(remove-duplicates (with-all-mts (isa " + \
##                cycFort.stringApiValue() + ")))")
##            else:
##                return self.converseList("(isa " + cycFort.stringApiValue() + \
##                " " + mt.stringApiValue() + ")")
##
##        def getGenlPreds (self, predicate, mt = None):
##            if mt == None:
##                return self.converseList("(remove-duplicates (with-all-mts (isa " + \
##                cycFort.stringApiValue() + ")))")
##            else:
##                return self.converseList("(isa " + cycFort.stringApiValue() + \
##                " " + mt.stringApiValue() + ")")
##
##        def getAllGenlPreds (self, predicate, mt = None):
##            if mt == None:
##                return self.converseList("(remove-duplicates (with-all-mts (isa " + \
##                cycFort.stringApiValue() + ")))")
##            else:
##                return self.converseList("(isa " + cycFort.stringApiValue() + \
##                " " + mt.stringApiValue() + ")")
##
##        def getAllSpecPreds (self, cycFort, mt = None):
##            # Why does this take a cycFort while getAllGenlPreds takes a CycConstant?
##            pass
##
##        def getAllSpecMts (self, mt):
##            if mt == None:
##                return self.converseList("(remove-duplicates (with-all-mts (isa " + \
##                cycFort.stringApiValue() + ")))")
##            else:
##                return self.converseList("(isa " + cycFort.stringApiValue() + \
##                " " + mt.stringApiValue() + ")")
#######################################

        # methods for fetching arg constraints go here

    def uncyclify (self, cycstring):
        return replace(cycstring,'#$','')

    def askWithVariable (self, query, variable, mt = None):
        queryBuffer = "(ask-template '" + variable.stringApiValue()
        queryBuffer = queryBuffer + " '" + query#.stringApiValue()
        queryBuffer = queryBuffer + " " + mt.stringApiValue() + ")"+"\r\n"
        return self.converseList(queryBuffer)

    def askWithVariables (self, query, variables, mt = None):
        varList = CycObject.CycList(variables)
        queryBuffer = "(ask-template '" + varList.stringApiValue()
        queryBuffer = queryBuffer + " '" + query#.stringApiValue()
        queryBuffer = queryBuffer + " " + mt.stringApiValue() + ")"+"\r\n"
        return self.converseList(queryBuffer)

    def makeCycList (self, string):
        return CycListParser.CycListParser(string).makeCycList()


# module CycConnection

DEFAULT_HOSTNAME = 'localhost'
DEFAULT_BASE_PORT = 3600
HTTP_PORT_OFFSET = 0
ASCII_PORT_OFFSET = 1
CFASL_PORT_OFFSET = 14
ASCII_MODE = 1
BINARY_MODE = 2
COMMUNICATION_MODE = ASCII_MODE
MESSAGING_MODE = 0 # code does not use this yet

class CycConnection(CycApiObject):

    def type (self): return 'CycConnection'

    def __init__ (self,
              hostName=DEFAULT_HOSTNAME,
              basePort=DEFAULT_BASE_PORT,
              communicationMode=COMMUNICATION_MODE,
              messagingMode=MESSAGING_MODE,
              cycAccess=None):
        self.hostName = hostName
        self.basePort = basePort
        self.asciiPort = basePort + ASCII_PORT_OFFSET
        self.communicationMode = communicationMode
        if communicationMode != ASCII_MODE:
            self.asciiSocket=0
        else: self.asciiSocket=''

        self.cycAccess = cycAccess

        self.initializeApiConnections()


    def __str__ (self):
        return(str([self.hostName,self.basePort,self.asciiPort,
                self.communicationMode,self.cycAccess,self.asciiSocket]))

    def initializeApiConnections (self):
        if self.communicationMode == ASCII_MODE:
            self.asciiSocket = socket(AF_INET, SOCK_STREAM)
            self.asciiSocket.connect((self.hostName, self.asciiPort))

    def close (self):
        if self.asciiSocket:
            self.asciiSocket.close()

    def converse (self, message, msglength=4096):
        if self.communicationMode == ASCII_MODE:
            if type(message) is str:
                # the following if isn't working
                if not message.endswith("\r\n"):
                    message += "\r\n"
                if self.cycAccess is None:
                    print "CycAccess is required to process commands"
                result = CycListParser(message).makeCycList()
                self.messageCycList = result[1]
            elif isinstance(message, CycObject.CycList):
                self.messageCycList = message

            sentBytes = self.asciiSocket.send(message)
            data = self.asciiSocket.recv(msglength)
            answerlist = split(rstrip(data),None,1)

            self.close()
            if answerlist[0] == '200':
                return [1, answerlist[1]]
            else:
                return "Error:",answerlist

    def uncyclify (self, cycstring):
        return replace(cycstring,'#$','')

