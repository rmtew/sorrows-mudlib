COMMAND_PLAYER    = 1
COMMAND_GAME      = 2
COMMAND_DEVELOPER = 4

commandLabels = [
    ("player",    COMMAND_PLAYER),
    ("game",      COMMAND_GAME),
    ("developer", COMMAND_DEVELOPER),
]

commandLabelsByAccessMask = {
    COMMAND_PLAYER:    "player",
    COMMAND_GAME:      "game",
    COMMAND_DEVELOPER: "developer",
}

class BaseCommand:
    def __init__(self, shell):
        self.shell = shell

    def Release(self):
        del self.shell

    def Run(self, verb, argString):
        pass


class PlayerCommand(BaseCommand):
    __access__ = COMMAND_PLAYER

class GameCommand(PlayerCommand):
    __access__ = COMMAND_GAME

    def Run(self, verb, argString):
        sorrows.parser.ExecuteGameCommand(self, verb, argString)

class DeveloperCommand(BaseCommand):
    __access__ = COMMAND_DEVELOPER

class CommandInfo:
    room = None
    body = None

    verb = None
    argString = None
