"""
This module is supposed to do useful things in the area of text formatting.
"""

import StringIO

def hcolumns(strings, width=80, marginSize=1, columnSize=None):
    if columnSize is None:
        columnSize = max(len(s) for s in strings) + marginSize
    currentWidth = 0
    sio = StringIO.StringIO()
    for s in strings:
        if currentWidth + columnSize > width:
            sio.write((width - currentWidth) * " ")
        sio.write(s)
        sio.write((columnSize - len(s)) * " ")
        currentWidth += columnSize
    return sio.getvalue()
