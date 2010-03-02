"""
This module is supposed to do useful things in the area of text formatting.
"""

import StringIO, logging

logger = logging.getLogger("textsupport")


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
    if number == 0:
        return "none"

    if number < 20:
        return [
            "one", "two", "three", "four", "five", "six", "seven", "eight",
            "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen"
        ][number]

    if number < 100:
        factor = (number / 10) - 2
        remainder = number % 10
        if remainder:
            remainderString = " "+ number_to_string(remainder)
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
        "ss": "sses",   # bus      -> busses
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
    logger.error("Failed to pluralise '%s'", noun)
    return noun +"s"

pluralize = pluralise   # American <- English
