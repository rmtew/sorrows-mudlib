# module CycAPI

import Cyc.CycConnection as CycConnection
import Cyc.CycObject as CycObject

def converse(msg = "(fi-ask '(#$isa #$Person ?WHAT) '#$InferencePSC)\r\n" ):
    cc = CycConnection.CycConnection('sparky.cyc.com',3620)
    ans = cc.converse(msg)
    return ans

def askWithVariable (query, var, mt):
    kb = CycConnection.CycAccess('sparky.cyc.com',3620)
    varObj = CycObject.CycVariable(var)
    mtObj = CycObject.CycConstant(mt)
    ans = kb.askWithVariable(query, varObj, mtObj)
    return ans.zopeApiValue()

def zopeApiListValue (arg):
    if arg['type'] == 'instance' and arg['class'] == 'CycList':
        result = []
        for item in arg['value']:
            result.append(zopeApiListValue(item))
    else:
        result = arg['value']
    return result

def zopeApiStringValue (arg):
    if arg['type'] == 'instance' and arg['class'] == 'CycList':
        stringBuffer = '('
        for item in arg['value']:
            stringBuffer = stringBuffer + zopeApiStringValue(item) + ' '
        result = stringBuffer[:-1] + ')'
    else:
        result = arg['value']
    return result

def zopeListOfStrings (zopeApiList):
    result = []
    for item in zopeApiList['value']:
        result.append(zopeApiStringValue(item))
    return result