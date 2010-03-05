"""
This module is supposed to do useful things in the area of text formatting.
"""

import StringIO


def hcolumns(strings, width=80, marginSize=1, leftMarginSize=2, columnSize=None):
    if columnSize is None:
        columnSize = max(len(s) for s in strings)
    columnSize += marginSize

    sio = StringIO.StringIO()
    sio.write(leftMarginSize * " ")
    currentWidth = leftMarginSize
    for s in strings:
        if currentWidth + columnSize > width:
            sio.write((width - currentWidth) * " ")
            sio.write(leftMarginSize * " ")
            currentWidth = leftMarginSize
        sio.write(s)
        sio.write((columnSize - len(s)) * " ")
        currentWidth += columnSize
    return sio.getvalue()


def number_to_words(number):
    if number < 20:
        return [
            "none", "one", "two", "three", "four", "five", "six", "seven", "eight",
            "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen"
        ][number]

    if number < 100:
        factor = (number / 10) - 2
        remainder = number % 10
        remainderString = ""
        if remainder:
            remainderString = " "+ number_to_words(remainder)
        return [
            "twenty", "thirty", "fourty", "fifty", "sixty", "seventy", "eighty", "ninety"
        ][factor] + remainderString

    if number < 1000:
        factor = (number / 100)
        remainder = number % 100
        parts = [ number_to_words(factor) +" hundred" ]
        if remainder:
            parts.append(number_to_words(remainder))
        return " and ".join(parts)

    if number < 1000000:
        factor = number / 1000
        remainder = number % 1000
        parts = [ number_to_words(factor) +" thousand" ]
        if remainder:
            parts.append(number_to_words(remainder))
        if remainder < 100:
            return " and ".join(parts)
        return ", ".join(parts)            

    factor = number / 1000000
    remainder = number % 1000000
    parts = [ number_to_words(factor) +" million" ]
    if remainder:
        parts.append(number_to_words(remainder))
    if remainder < 100:
        return " and ".join(parts)
    return ", ".join(parts)            


def pluralise(noun):
    plural = {
        "bison": "bison",
        "goose": "geese",  # Irregular nouns
        "moose": "moose",
        "mouse": "mice",
        "ox":    "oxen",
        "sheep": "sheep",
        "foot":  "feet",
        "tooth": "teeth",
        "man":   "men",
        "woman": "women",
        "child": "children",
    }.get(noun, None)
    if plural is not None:
        return plural

    sEnding = noun[-2:]
    pEnding = {
        "ss": "sses",   # moss     -> mosses
        "zz": "zzes",   # ?
        "sh": "shes",   # bush     -> bushes
        "ch": "ches",   # branch   -> branches
        "fe": "ves",    # knife    -> knives
        "ff": "ffs",    # cliff    -> cliffs

        "ay": "ays",    # <vowel>y -> <vowel>ys
        "ey": "eys",    #
        "iy": "iys",    #
        "oy": "oys",    #
        "uy": "uys",    #
    }.get(sEnding, None)
    if pEnding is not None:
        return noun[:-2] + pEnding

    sEnding = noun[-1]
    pEnding = {
        "y": "ies",     # family   -> families
        "f": "ves",     # loaf     -> loaves
    }.get(sEnding, None)
    if pEnding is not None:
        return noun[:-1] + pEnding

    pEnding = {
        "s": "",        # pants    -> pants
        "x": "es",      # fox      -> foxes
    }.get(sEnding, None)
    if pEnding is not None:
        return noun + pEnding

    # Fallback case.
    return noun +"s"

pluralize = pluralise   # American <- English

if __name__ == "__main__":    
    import unittest

    class NumberWordificationTests(unittest.TestCase):
        def testLessThanOneHundred(self):
            self.failUnlessEqual(number_to_words(0), "none")
            self.failUnlessEqual(number_to_words(1), "one")
            self.failUnlessEqual(number_to_words(5), "five")
            self.failUnlessEqual(number_to_words(10), "ten")
            self.failUnlessEqual(number_to_words(15), "fifteen")
            self.failUnlessEqual(number_to_words(20), "twenty")
            self.failUnlessEqual(number_to_words(21), "twenty one")
            self.failUnlessEqual(number_to_words(50), "fifty")

        def testHundreds(self):
            self.failUnlessEqual(number_to_words(100), "one hundred")
            self.failUnlessEqual(number_to_words(101), "one hundred and one")
            self.failUnlessEqual(number_to_words(111), "one hundred and eleven")
            self.failUnlessEqual(number_to_words(199), "one hundred and ninety nine")
            self.failUnlessEqual(number_to_words(999), "nine hundred and ninety nine")

        def testThousands(self):
            self.failUnlessEqual(number_to_words(1000), "one thousand")
            self.failUnlessEqual(number_to_words(1001), "one thousand and one")
            self.failUnlessEqual(number_to_words(1099), "one thousand and ninety nine")
            self.failUnlessEqual(number_to_words(1100), "one thousand, one hundred")
            self.failUnlessEqual(number_to_words(1101), "one thousand, one hundred and one")
            self.failUnlessEqual(number_to_words(11101), "eleven thousand, one hundred and one")
            self.failUnlessEqual(number_to_words(100101), "one hundred thousand, one hundred and one")
            self.failUnlessEqual(number_to_words(101101), "one hundred and one thousand, one hundred and one")
            
        def testMillions(self):
            self.failUnlessEqual(number_to_words(1000000), "one million")
            self.failUnlessEqual(number_to_words(1000001), "one million and one")
            self.failUnlessEqual(number_to_words(1900000), "one million, nine hundred thousand")
            self.failUnlessEqual(number_to_words(1900001), "one million, nine hundred thousand and one")

    class PluralisationTests(unittest.TestCase):
        def testSelectionOfCases(self):
            # One of the irregular nouns.    
            self.failUnlessEqual(pluralise("man"), "men")
            # Something other cases.
            self.failUnlessEqual(pluralise("moss"), "mosses")
            self.failUnlessEqual(pluralise("cliff"), "cliffs")    
            self.failUnlessEqual(pluralise("knife"), "knives")
            self.failUnlessEqual(pluralise("boy"), "boys")
            self.failUnlessEqual(pluralise("grey"), "greys")
            self.failUnlessEqual(pluralise("gray"), "grays")
            self.failUnlessEqual(pluralise("nappy"), "nappies")
            self.failUnlessEqual(pluralise("pants"), "pants")
            self.failUnlessEqual(pluralise("fox"), "foxes")
            # The fallback case.
            self.failUnlessEqual(pluralise("chest"), "chests")

    unittest.main()
