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
