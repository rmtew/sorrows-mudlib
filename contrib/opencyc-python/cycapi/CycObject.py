# module CycObject

import string
import CycConnection

DEFAULT_SERVER_HOST = 'localhost'
DEFAULT_BASE_PORT = 3600
SERVER_HOST = 'sparky.cyc.com'
BASE_PORT = 3620
CACHE_ENGLISH = 0
PRECOMPUTE_ENGLISH_FOR_ZOPE = 1

## We need to support cacheing and precomputing of english for FORTs and for
## assertions. We should use methods toEnglish (public) and _toEnglish (private).

class ConnectionClient:

    def __init__ (self):
        pass

    # Would it work to turn the following into a class variable, created once
    # and used continuously?
    def getCycServerHandle (self, serverHost=SERVER_HOST, basePort=BASE_PORT):
        return CycConnection.CycAccess(serverHost, basePort)

class List (ConnectionClient):

    def __init__ (self, data=None):
        if data == None:
            data = []
        self.data = data

    def __getitem__ (self, i):
        return self.data[i]

    def __setitem__ (self, i, val):
        self.data[i] = val

    def __delitem__ (self, i):
        del self.data[i]

    def __len__ (self):
        return len (self.data)
        
    def __str__ (self):
        result = '['
        for item in self.data:
            result = result + str(item) + ' '
        result = result[:-1] + ']'
        return result
        
    def first (self):
        return self[0]
        
    def rest (self):
        return self[1:]


class CycObject (ConnectionClient):
    
    def __init__ (self):
        pass

    def __str__ (self):
        return "<CycObject>"
 
    def cyclify (self):
        return str(self)

    def zopeApiValue (self):
        resultDict = {}
        resultDict['type'] = 'instance'
        resultDict['class'] = 'CycObject'
        resultDict['value'] = self.cyclify()
        return resultDict

class CycFort (CycObject):

    def __init__ (self,id=None):
	CycObject.__init__(self)
    	self.id = id
    	
    def safeToString (self):
        pass

    def english (self):
        kb = self.getCycServerHandle()
        return kb.getGeneratedPhrase(self)

    def setID (self, id):
        self.id = id

    def getID (self):
        return self.id
    
    #def compareTo (object):

class Guid:
    def __init (self, guidString):
        self.guidString = guidString
        
    def toString (self):
        return self.guidString

class CycConstant (CycFort):

    def __init__ (self, name = None, guid = None, id = None):
	CycFort.__init__(self)
        if name != None and name[:1] == "#$":
            self.name = self.name[2:]
        else:
            self.name = name
        self.guid = guid
        
    def __str__ (self):
        return self.name

    def stringApiValue (self):
        return self.cyclify()

    def zopeApiValue (self):
        resultDict = {}
        resultDict['type'] = 'instance'
        resultDict['class'] = 'CycConstant'
        resultDict['value'] = self.stringApiValue()
        return resultDict

    def cyclify (self):
        return '#$'+self.name

    def getName (self):
        return self.name

    def setName (self, name):
        self.name = name

    def getGuid (self):
        return self.guid

    def setGuid (self):
        self.guid = guid

    # don't use hashCode(); instead, use dict if possible

    def equals (self, other):
        if not (type(other) == 'instance') and not isinstance(other, CycConstant):
            return 0
        thisID = self.getID()
        thatID = other.getID()
        if (thisID != None) and (thatID != None):
            return thisID == thatID
        thisName = self.getName()
        thatName = other.getName()
        if (thisName != None) and (thatName != None):
            return thisName == thatName
        return 0


class CycNart (CycFort):
    
    functor = None
    arguments = None
    
    def __init__ (self, arg1 = None, arg2 = None, arg3 = None):
        CycFort.__init__(self)
	if arg1 == None:
		self.functor = None
		self.arguments = CycList([])
	elif arg2 == None:
		if not (type(arg1)=='instance') or not isinstance(arg1, CycList):
			raise TypeError, 'arg1 is not an instance of CycList'
		if not isinstance(arg1.first(), CycFort):
			raise TypeError, 'arg1 is not an instance of CycFort'
		self.functor = cycList.first()
		self.arguments.addAll(cycList.rest())
	elif arg3 != None:
		self.functor = arg1
		self.arguments = CycList(arg2, arg3)
	else:
		self.functor = arg1
		self.arguments = CycList(arg2)
        
    def coerceToCycNart (self, object):
        if type(object) == 'instance':
            if isinstance(object, CycNart):
                return object
            if not isinstance(object, CycList):
                raise TypeError, 'object is not an instance of CycList'
            return CycNart(object)

    def getFunctor (self):
        # used by binary API only
        pass
        
    def setFunctor (self, functor):
        self.functor = functor
        
    def getArguments (self):
        if arguments == None:
            raise NotImplementedError, 'getArguments for binary API not yet supported'
        return self.arguments
        
    def setArguments (self):
        self.arguments = arguments
        
    def toCycList (self):
        return CycList(self.functor, self.arguments)
        
    def toString (self):
        pass
        
    def cyclify (self):
        return self.toCycList().cyclify()
        
    def safeToString (self):
        result = ''
        if self.functor != None:
            result = result + self.functor.safeToString()
        else:
            result = result + '<uncomplete functor>'
        for e in self.arguments:
            safeObject = None
            if type(e) == 'instance' and isinstance(e, CycFort):
                safeObject = e.safeToString()
            else:
                safeObject = e.toString()
            result = result + " " + safeObject
        return result + ")"
        
    def stringAPIValue (self):
        return self.toCycList.stringApiValue()
        
    def zopeApiValue (self):
        resultDict = {}
        resultDict['type'] = 'instance'
        resultDict['class'] = 'CycNart'
        value = {}
        value['functor'] = self.functor.zopeApiValue()
        value['arguments'] = self.arguments.zopeApiValue()
        resultDict['value'] = value
        return resultDict

    def cycListApiValue (self):
        pass
        
    def metaGuid (self):
        pass
        
    def metaName (self):
        pass
        
    def equals (self, object):
        pass
    
    def hasFunctorAndArgs (self):
        return (self.functor != None) and (self.arguments != None)
        

# I want to make CycList a subclass of the Python built-in type 'list'.
# This is supported in Python 2.2, but Zope does not yet support Python 2.2.
# So, to stay compatible with Zope, we won't subclass built-in types...yet.

# Also, I'd like to use function overloading as in the Java API
# (e.g. have multiple __init__ methods with different parm types),
# but Python doesn't support it. So I'll use one __init__ method
# with generic parm var names and I'll test their types to determine
# which code to run.
class CycList (List):

    def __init__ (self, arg1, arg2 = None):
	"""
	"""
	List.__init__(self)
#	print "IN CYCLIST INITIALIZATION"
        if arg2 == None:
            if type(arg1) == type([]) or \
               ((str(type(arg1)) == "<type 'instance'>") and isinstance(arg1,CycList)):
#                print "USING THIS CYCLIST INITIALIZATION ROUTINE"
		# Constructs a new <tt>CycList</tt> object, containing the 
		# elements of the specified collection, in the order they 
		# are returned by the collection's iterator.
                #
		# arg1 is a set (implemented as a list) of assumed valid
		# OpenCyc objects.
                self.data = arg1
        elif (str(type(arg1)) == "<type 'instance'>") and isinstance(arg1,CycObject):
                # Constructs a new <tt>CycList</tt> object, containing as
                # its sole element <tt>arg1</tt>.
                self.data = [arg1]
        elif (str(type(arg2)) == "<type 'instance'>") and isinstance(arg2,List):
            # Constructs a new <tt>CycList</tt> object, containing as its first
            # element <tt>arg1</tt>, and containing as its remaining elements
            # the contents of the elements in the collection <tt>arg2</tt>.
            self.data = arg2.insert(0, arg1)
        else:
            # Constructs a new <tt>CycList</tt> object, containing as its
            # first element <tt>arg1</tt> and <tt>arg2</tt> as its 
            # second element.
            #
            # arg 2 can be anything, including an int or a string
            self.data = [arg1, arg2]
    
    def construct (self, object1, object2):
        pass

    def __str__ (self):
        result = '('
        for item in self.data:
            result = result + str(item) + ' '
        result = result[:-1] + ')'
        return result

    def cyclify (self):
        result = '('
        for item in self.data:
            if (str(type(arg1)) == "<type 'instance'>") and isinstance(arg1,CycObject):
                result = result + self.cyclify() + ' '
            elif type(item) == type(''):
                result = result + self + ' '
            else:
                result = result + str(self) + ' '
        result = result[:-1] + ')'
        return result

    def stringApiValue (self):
        result = '('
        for item in self.data:
            result = result + item.stringApiValue() + ' '
        result = result[:-1] + ')'
        return result

    def zopeApiValue (self):
        resultDict = {}
        resultDict['type'] = 'instance'
        resultDict['class'] = 'CycList'
        value = []
        for item in self.data:
            value.append(item.zopeApiValue())
        resultDict['value'] = value
        return resultDict

    def clone (self):
        pass
        
    def deepCopy (self):
        pass
        
    def getDottedElement (self):
        pass
        
    def setDottedElement (self, dottedElement):
        pass
        
    def isValid (self):
        pass
        
    def isFormulaWellFormed (self):
        pass
        
    def isCycLNonAtomicReifiableTerm (self):
        pass
        
    def isCycLNonAtomicUnreifiableTerm (self):
        pass
    
    def first (self):
        pass


class CycVariable (CycObject):

    def __init__ (self, name = None, id = None):
        if name != None:
            if name[0] == "?":
                self.name = name[1:]
            else:
                self.name = name
                
    def __str__ (self):
        return '?' + self.name

    def toString(self):
        return self.cyclify()

    def safeToString (self):
        if self.name != None:
            return name
        stringBuffer = "[CycVariable "
        if (self.id != None):
            stringBuffer = stringBuffer + "id: " + id + "]"
        return self.toString()

    def cyclify (self):
        return "?" + self.name

    def stringApiValue (self):
        return self.cyclify()

    def zopeApiValue (self):
        resultDict = {}
        resultDict['type'] = 'instance'
        resultDict['class'] = 'CycVariable'
        resultDict['value'] = self.stringApiValue()
        return resultDict

    def cycListApiValue (self):
        return self

    def equals (self, other):
        if (type(other) == 'instance') and isinstance(other, CycVariable):
            return self.name == other.name
        else:
            return false

    def compareTo (self, other):
        """CycVariable.compareTo() is not yet implemented"""
        return 0

class CycSymbol (CycObject):

    def __init__ (self, symbolName):
        self.symbolName = symbolName
        
    def __str__ (self):
        return self.toString()

    def toString (self):
        return self.symbolName

    def zopeApiValue (self):
        resultDict = {}
        resultDict['type'] = 'instance'
        resultDict['class'] = 'CycSymbol'
        resultDict['value'] = self.toString()
        return resultDict

    def equals (self, other):
        if (type(other) == 'instance') and isinstance(other, CycSymbol):
            return self.symbolName == other.symbolName
        else:
            return false

    def isKeyword (self):
        return self.symbolName[0] == ":"

    def compareTo (self):
        """CycSymbol.compareTo() is not yet implemented"""
        return 0

    def isValidSymbolName (self, testString):
        stringOfValidChars = string.digits + string.letters + "-_*?:"
        for c in testString:
            if string.find(stringOfValidChars, c) == -1:
                return 0
        return 1
        
class CycAssertion (CycObject):
    
    def __init__ (self, formula):
        self.id = None
        if formula == None:
            self.formula = None
        elif type(formula) == type(''):
            self.formula = CycListParser(formula).makeCycList()
        elif (type(command) == 'instance') and isinstance(command, CycList):
            self.formula = formula
        
    def equals (self, other):
        if type(other) != 'instance':
            return false
        elif not isinstance(other, CycConnection.CycAccess):
            return false
        elif other.id != None:
            return self.id == other.id
            
    def __str__ (self):
        if formula == None:
            return "assertion with id:", self.id
        else:
            return formula.cyclify()
            
    def toString (self):
        return self.__str__()
        
    def safeToString (self):
        stringBuffer = '[assertion '
        if self.id != None:
            stringBuffer = stringBuffer + 'id: ' + str(self.id)
        stringBuffer = stringBuffer + ']'
        return stringBuffer
        
    def stringApiValue (self):
        self.formula.cyclify()

    def zopeApiValue (self):
        resultDict = {}
        resultDict['type'] = 'instance'
        resultDict['class'] = 'CycAssertion'
        value = []
        for item in self.formula.data:
            value.append(item.zopeApiValue())
        resultDict['value'] = value
        return resultDict

    def cycListApiValue (self):
        return self
