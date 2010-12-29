#
# IDEA:
# - Maybe remove line numbers and replace them with labels.
#
#

import re, logging


LINE_TEMPLATE = "(?P<lineNumber>[0-9]{3})\. (?P<timeHours>[0-9]{2}):(?P<timeMinutes>[0-9]{2}):(?P<timeSeconds>[0-9]{2}) (?P<command>.*)"
LINE_RE = re.compile(LINE_TEMPLATE)


COMMAND_TEMPLATE = "ob\s+(?P<name>[a-zA-Z_]\w*)\s+=\s+(?P<command>[a-zA-Z_]\w*)"
COMMAND_RE = re.compile(COMMAND_TEMPLATE)
ACTOR_COMMAND_TEMPLATE = "(?P<actor>[a-zA-Z_]\w*): (?P<command>.*)"
ACTOR_COMMAND_RE = re.compile(ACTOR_COMMAND_TEMPLATE)
ACTOR_OBSERVATION_TEMPLATE = "(?P<actor>[a-zA-Z_]\w*)\.\. (?P<observation>.*)"
ACTOR_OBSERVATION_RE = re.compile(ACTOR_OBSERVATION_TEMPLATE)


class TranscriptCommand(object):
    def __init__(self, variableName, variableCommand):
        self.variableName = variableName
        self.variableCommand = variableCommand

class TranscriptActorCommand(object):
    def __init__(self, variableName, variableCommand):
        self.variableName = variableName
        self.variableCommand = variableCommand

class TranscriptActorObservation(object):
    def __init__(self, variableName, variableObservation):
        self.variableName = variableName
        self.variableCommand = variableCommand


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

        match = COMMAND_RE.match(line)
        if match is not None:
            logging.root.info("COMMAND: name = %s", match.group("name"))
            logging.root.info("COMMAND: command = %s", match.group("command"))
            self.lines.append(TranscriptCommand(command))
            return

        match = ACTOR_COMMAND_RE.match(line)
        if match is not None:
            logging.root.info("COMMAND: actor = %s", match.group("actor"))
            logging.root.info("COMMAND: command = %s", match.group("command"))
            self.lines.append(TranscriptActorCommand(command))
            return

        match = ACTOR_OBSERVATION_RE.match(line)
        if match is not None:
            logging.root.info("OBSERVATION: actor = %s", match.group("actor"))
            logging.root.info("OBSERVATION: command = %s", match.group("observation"))
            self.lines.append(TranscriptActorObservation(command))
            return

        raise RuntimeError("Invalid transcript")        

    def Run(self):
        pass

