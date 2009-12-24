# Unit test the telnet negotiation module.

import unittest
import telnetnegotiation
from telnetnegotiation import TelnetNegotiation
original_IAC = telnet.IAC

class FeedTests(unittest.TestCase):
    def setUp(self):
        telnet.IAC = "C"

        class HobbledTelnetNegotiation(TelnetNegotiation):
            def _negotiation(self, byte):
                return byte == "C"

        self.negotiator = HobbledTelnetNegotiation()
        
    def tearDown(self):
        telnet.IAC = original_IAC

    def find_untainted_bits(self, bits, taint="TAINT"):
        for bit in bits:
            if taint not in bit:
                yield bit 

    def checkFeedResult(self, original_bits):
        expected_bits = list(self.find_untainted_bits(original_bits, taint="C"))
        data = "".join(original_bits)        
        actual_bits = list(self.negotiator.feed(data))
        self.failUnless(actual_bits == expected_bits, "Option characters still present in %s" % actual_bits)
                
    def testFindUntaintedBits(self):
        original_bits = [ "DDDD", "CC", "D", "C", "DDD" ]
        untainted_bits = list(self.find_untainted_bits(original_bits, taint="C"))
        self.failUnless([ "DDDD", "D", "DDD" ] == untainted_bits, "find_untainted_bits returned crap: %s" % untainted_bits)        

    def testFeedOptionRemovalLeadingTextCharacter(self):
        self.checkFeedResult([ "D", "CCCCCCCC" ])
        
    def testFeedOptionRemovalLeadingTextCharacters(self):
        self.checkFeedResult([ "DD", "CCCCCCCC" ])
        
    def testFeedOptionRemovalTrailingTextCharacter(self):
        self.checkFeedResult([ "CCCCCCCC", "D" ])

    def testFeedOptionRemovalTrailingTextCharacters(self):
        self.checkFeedResult([ "CCCCCCCC", "DD" ])

    def testFeedOptionRemovalEmbeddedTextCharacter(self):
        self.checkFeedResult([ "CCCCCCCC", "D", "CCCCCC" ])

    def testFeedOptionRemovalEmbeddedTextCharacters(self):
        self.checkFeedResult([ "CCCCCCCC", "DD", "CCCCCC" ])
        
    def testFeedOptionRemovalSurroundingTextCharacter1(self):
        self.checkFeedResult([ "D", "C", "D" ])

    def testFeedOptionRemovalSurroundingTextCharacter2(self):
        self.checkFeedResult([ "D", "CC", "D" ])

    def testFeedOptionRemovalSurroundingTextCharacters(self):
        self.checkFeedResult([ "DD", "CC", "DD" ])
        
if __name__ == "__main__":
    unittest.main()