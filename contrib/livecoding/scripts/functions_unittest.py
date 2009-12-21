import unittest

class TestFunctionTests(unittest.TestCase):
    def testTestFunction(self):        
        if unitTestFailure:
            self.failUnless(TestFunction("str")[0] != "str", "TestFunction returned unexpected results")
        else:
            self.failUnless(TestFunction("str")[0] == "str", "TestFunction returned unexpected results")
