#
# IDEA:
# - Maybe remove line numbers and replace them with labels.
#
#

import re, logging

LINE_TEMPLATE = "(?P<lineNumber>[0-9]{3})\. (?P<timeHours>[0-9]{2}):(?P<timeMinutes>[0-9]{2}):(?P<timeSeconds>[0-9]{2}) (?P<command>.*)"
LINE_RE = re.compile(LINE_TEMPLATE)

class Transcript(object):
    def __init__(self):
        self.lines = []

    def ReadFile(self, filePath):
        # Prepare the file for execution.
        with open(filePath, "r") as f:
            line = f.readline()
            while line != "":
                line = line.strip()
                self._ProcessLine(line)
                line = f.readline()

    def _ProcessLine(self, line):
        match = LINE_RE.match(line)
        if match is None:
            return

        lineNumber = match.group("lineNumber")      # Ignore this for now.
        timeHours = match.group("timeHours")        # Ignore these for now.
        timeMinutes = match.group("timeMinutes")
        timeSeconds = match.group("timeSeconds")
        command = match.group("command")

        logging.root.info("LINE %s", command)
