# module CycList Parser

from string import find, index, index_error, replace, rfind, split
import CycObject


class CycListParser:

    def __init__ (self, inString, index = 0):
        s = self
        s.resultList = []
        s.handlerDict = HandlerDict(self)
        s.quoteLevel = 0

        if inString[index] == '(':
            s.inString = inString
            s.inStringLength = len(s.inString)
        else:
            raise TypeError, "Expected string surrounded by '(' and ')', got "+ str(inString)

    def test(self,testPoint, stringPtr = 999):
        pass
#        s = self
#        if len(s.resultList)>0:
#            lastItem = s.resultList[len(s.resultList)-1]
#        else:
#            lastItem = '*empty*'
#        print "TEST POINT",str(testPoint)
#        print "String pointer:", stringPtr, s.inString[stringPtr], lastItem, str(testPoint)
#        print "resultList:", self.resultList
#        print "lastItem:", lastItem
#        print "---------------"

    def makeCycList (self, startPtr = 0):
        s = self
        i = startPtr + 1
        s.test('makeCycList',i)

        while i < s.inStringLength:
            if s.inString[i] == ')':
                i = i + 1
                break
            elif s.inString[i] == '(':
                result = CycListParser(s.inString[i:]).makeCycList()
                i = result[0] + i
                s.resultList.append(result[1])
            else:
                i = s.handleChar(i)
        cycList = CycObject.CycList(s.resultList)
#        print "CYCLIST.data =",cycList.data
        return i, cycList

    def handleChar (self, startPtr):
        s, i = self, startPtr
        key = s.inString[i]
        s.test('handleChar',i)
        if s.handlerDict.hasHandler(key):
            handler = Handler(s.handlerDict, key)
            s.test('handleChar: there is a handler',i)
            # the handler pushes a token onto resultList and advances the pointer 'i'
            i = handler.function(i)
            s.test('handleChar - after executing handler function',i)
        else: #no handler function; treat as symbol terminated by any 'handled' token
            i = s.handleSymbol(i)
        return i

    def handleSymbol (self, startPtr):
        s, i = self, startPtr
        s.test('handleSymbol',i)
        while i < s.inStringLength and not s.handlerDict.hasHandler(s.inString[i]):
            i = i + 1
            s.test('handleSymbol - in while loop',i)
        symbolName = s.inString[startPtr:i]
        newToken = CycObject.CycSymbol(symbolName)
        s.resultList.append(newToken)
        return i

    def handleSpaceChar (self, startPtr):
        self.test('handleSpaceChar - exit value',startPtr+1)
        return startPtr + 1

    def handleLeftParens (self, startPtr):
        self.test('BEGIN handleLeftParens',startPtr)
        s,i = self, startPtr
        if self.quoteLevel == 0:
            i = self.makeCycList(startPtr + 1)
            self.test('FINISH handleLeftParens',i)
            return i
        else:
            raise ValueError, "Treating '(' within string like a token"

    def handleRightParens (self, startPtr):
        raise ValueError,"handleRightParens should never be called"

    def handleDoubleQuoteChar (self, startPtr):
        s, i = self, startPtr
        s.quoteLevel = s.quoteLevel + 1
        i = startPtr + 1
        while i < s.inStringLength and s.inString[i] != '"':
            i = i + 1
        if i-1 > startPtr:
            newToken = s.inString[startPtr+1:i-1]
            s.resultList.append(newToken)
        else:
            pass
        s.quoteLevel = s.quoteLevel - 1
        return i

    def handleQuestionMark (self, startPtr):
        s, i = self, startPtr
        i = s.handleSymbol(startPtr+1)
        #pop last token, convert to variable, then push again
        newestSymbol = s.resultList.pop()
        s.test('handleQuestionMark: symbolName: ' + newestSymbol.symbolName,i)
        newToken = CycObject.CycVariable(newestSymbol.symbolName)
        s.resultList.append(newToken)
        return i

    def handleHashChar (self, startPtr):
        s, i = self, startPtr
        s.test('BEGIN handleHashChar',i)
        if i+1 < s.inStringLength:
            if s.inString[i + 1] == '$':
                i = s.handleHashDollar(i)
            else:
                i = s.handleSymbol(i)
        else:
            s.resultList.append('#')
            i = i + 1
        return i

    def handleHashDollar (self, startPtr):
        s, i = self, startPtr
        s.test('BEGIN handleHashDollar',i)
        if i + 2 < s.inStringLength:
            i = s.handleSymbol(i+2)
            #pop last token, convert to CycConstant, then push it back
            newestSymbol = s.resultList.pop()
            newToken = CycObject.CycConstant(newestSymbol.symbolName)
            s.resultList.append(newToken)
        else:
            s.resultList.append('#$')
        s.test('FINISH handleHashDollar',i)
        return i

    def handleMultiCharToken (self, startPtr):
        pass


class Handler:
    def __init__ (self, dict, key):
        if dict.hasHandler(key):
            self.function = dict.getHandlerFunction(key)
        else:
            raise ValueError, "No handler in handlerDict for", key

class HandlerDict:

    def __init__ (self,parser):
        self.handlerDict = {'(':[parser.handleLeftParens],
                            ')':[parser.handleRightParens],
                            '"':[parser.handleDoubleQuoteChar],
                            '\\':[parser.handleMultiCharToken],
                            ' ':[parser.handleSpaceChar],
                            '?':[parser.handleQuestionMark],
                            '#':[parser.handleHashChar]}

    def hasHandler (self,key):
        return self.handlerDict.has_key(key)

    def getHandlerFunction (self, key):
        return self.handlerDict[key][0]
