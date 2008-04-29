# module CycKnowledgePopulator

import Cyc.CycRKP as CycRKP
import Cyc.CycObject as CycObject

def findUnitsForPred (predString):
    pred = CycObject.CycConstant(predString)
    kp = CycRKP.CycKnowledgePopulator('sparky.cyc.com',3620)
    ans = kp.findUnitsForPred(pred)
    return ans.zopeApiValue()

def findCollectionPredicates (collectionString):
    collection = CycObject.CycConstant(collectionString)
    kp = CycRKP.CycKnowledgePopulator('sparky.cyc.com',3620)
    ans = kp.findCollectionPredicates(collection)
    return ans.zopeApiValue()
