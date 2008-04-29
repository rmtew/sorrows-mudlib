
colourByName = {
    'reset':    0,
    'black':   30,
    'red':     31,
    'green':   32,
    'yellow':  33,
    'blue':    34,
    'purple':  35,
    'cyan':    36,
    'white':   37,
    'Black':   40,
    'Red':     41,
    'Green':   42,
    'Yellow':  43,
    'Blue':    44,
    'Purple':  45,
    'Cyan':    46,
    'White':   47,
}

def AnsiText(text, colour="reset", invert=0, bold=0, light=0):
    prefix = ""
    if invert:
        prefix += "7;"
    if bold:
        prefix += "1;"
    if light:
        prefix += "2;"
    prefix += "%d" % colourByName[colour]
    return "\x1B[%sm%s\x1B[0m" % (prefix, text)
