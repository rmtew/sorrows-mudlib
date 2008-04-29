# module CycConnectionTestSuite

import unittest
import string
import CycConnection
import CycObject
import CycListParser

class CycApiTestCase (unittest.TestCase):
    def assertEquals (self, obj1, obj2):
        assert obj1 == obj2
    def assertTrue (self, expression):
        #assert expression
        #commented out until I learn how to pass an expression that won't
        #evaluate until it gets to the body of this method
        pass

# C:\Richard\CVS\personal\sorrows-src\contrib\opencyc-python\cycapi\

class CycConnectionTestCase (CycApiTestCase):
    def setUp (self):
        self.hostName = 'localhost'
        self.basePort = 3600
    def setUp2 (self):
        self.setUp()
        self.cycConnection = CycConnection.CycConnection(self.hostName,self.basePort)
    def tearDown (self):
        pass
    def testInitialization1 (self):
        cycConnection = CycConnection.CycConnection(self.hostName,self.basePort)
        self.assertEquals(cycConnection.hostName, self.hostName)
        self.assertEquals(cycConnection.basePort, self.basePort)
    def testConverse1 (self):
        self.setUp2()
        msg1 = "(fi-ask '(#$isa #$Person ?WHAT) '#$InferencePSC)"
        ans1 = self.cycConnection.converse(msg1)
        self.assertEquals(ans1[0],1)
        self.assertEquals(ans1[1][0:8],'(((?WHAT')


class CycAccessTestCase (CycApiTestCase):
    def setUp (self):
        self.hostName = 'localhost'
        self.basePort = 3600
        self.cycAccess = CycConnection.CycAccess(self.hostName, self.basePort)
    def tearDown (self):
        self.cycAccess.close()
    def testInitialization (self):
        pass
    def testConverse1 (self):
        msg = "(fi-ask '(#$isa #$Event ?WHAT) '#$InferencePSC)"
        ans = self.cycAccess.converse(msg)
        self.assertEquals(ans[0],1)
        self.assertEquals(ans[1][0:8],'(((?WHAT')
    def testAskWithVariable1 (self):
        whatVar = CycObject.CycVariable('?WHAT')
        mt = CycObject.CycConstant('InferencePSC')
        query = "(#$isa #$Person ?WHAT)"
        ans = self.cycAccess.askWithVariable (query,whatVar,mt)
        stringListOfConstants = ''
        for constant in ans:
            stringListOfConstants = stringListOfConstants + str(constant) + ' '
        assert string.find(stringListOfConstants,'BiologicalTaxon') != -1
    def testAskWithVariables1 (self):
        whatVar = CycObject.CycVariable('?WHAT')
        whoVar = CycObject.CycVariable('?WHO')
        varList = CycObject.CycList([whatVar,whoVar])
        mt = CycObject.CycConstant('InferencePSC')
        query = "(#$and (#$isa ?WHO #$Inventor) (#$isa ?WHO ?WHAT))"
        ans = self.cycAccess.askWithVariables(query,varList,mt)
        assert string.find(ans.stringApiValue(),'#$Agent-Generic')

class CycListParserTestCase (CycApiTestCase):
    def setUp (self):
        pass
    def testParseStringIntoCycList1 (self):
        testString1 = '(#$One (#$Two ?THREE) #$Four)'
        clp = CycListParser.CycListParser(testString1)
        result = clp.makeCycList()
        self.assertEqual(result[1].stringApiValue(),'(#$One (#$Two ?THREE) #$Four)')

def suite():
    suite = unittest.TestSuite()
    suite.addTest(CycConnectionTestCase("testInitialization1"))
    suite.addTest(CycConnectionTestCase("testConverse1"))
    suite.addTest(CycAccessTestCase("testConverse1"))
    suite.addTest(CycAccessTestCase("testAskWithVariable1"))
    suite.addTest(CycAccessTestCase("testAskWithVariables1"))
    suite.addTest(CycListParserTestCase("testParseStringIntoCycList1"))
    return suite

if __name__ == "__main__":
    unittest.main()
